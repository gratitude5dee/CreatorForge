"""Mindra orchestration API client."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

import httpx


@dataclass(frozen=True)
class MindraApproval:
    approval_id: str
    tool_name: str | None
    tool_input: dict | None


@dataclass(frozen=True)
class MindraExecutionResult:
    execution_id: str
    stream_url: str
    status: str
    final_answer: str | None = None
    chunks: list[str] = field(default_factory=list)
    tool_events: list[dict] = field(default_factory=list)
    approvals: list[MindraApproval] = field(default_factory=list)


class MindraClient:
    """Calls Mindra workflow APIs and consumes SSE execution streams."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        creative_workflow_slug: str,
        procurement_workflow_slug: str,
        connect_timeout_seconds: int,
        read_timeout_seconds: int,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.creative_workflow_slug = creative_workflow_slug
        self.procurement_workflow_slug = procurement_workflow_slug
        self.timeout = httpx.Timeout(read_timeout_seconds, connect=connect_timeout_seconds)

    def run_creative_workflow(self, trace_id: str, context: dict) -> MindraExecutionResult:
        task = f"Run CreatorForge creative workflow for {context.get('service', 'asset generation')}"
        return self._run_workflow(self.creative_workflow_slug, trace_id, task, context)

    def run_procurement_workflow(self, trace_id: str, context: dict) -> MindraExecutionResult:
        task = f"Run CreatorForge procurement workflow for {context.get('objective', 'external buying')}"
        return self._run_workflow(self.procurement_workflow_slug, trace_id, task, context)

    def approve_execution(self, execution_id: str, approval_id: str, reason: str | None = None) -> dict:
        return self._decision("approve", execution_id, approval_id, reason)

    def reject_execution(self, execution_id: str, approval_id: str, reason: str | None = None) -> dict:
        return self._decision("reject", execution_id, approval_id, reason)

    def _decision(self, action: str, execution_id: str, approval_id: str, reason: str | None) -> dict:
        url = f"{self.base_url}/v1/workflows/execute/{execution_id}/{action}/{approval_id}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                url,
                headers=self._headers(),
                json={"reason": reason} if reason else {},
            )
        response.raise_for_status()
        return response.json()

    def _run_workflow(self, workflow_slug: str, trace_id: str, task: str, metadata: dict) -> MindraExecutionResult:
        payload = {"task": task, "metadata": {"trace_id": trace_id, **metadata}}

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/v1/workflows/{workflow_slug}/run",
                        headers=self._headers(),
                        json=payload,
                    )
                response.raise_for_status()
                run_payload = response.json()
                execution_id = run_payload["execution_id"]
                stream_url = run_payload["stream_url"]
                return self._consume_stream(execution_id, stream_url)
            except Exception as exc:  # pragma: no cover - network path
                last_error = exc
                if attempt < 2:
                    time.sleep(2 ** attempt)

        raise RuntimeError(f"Mindra orchestration failed after retries: {last_error}")

    def _consume_stream(self, execution_id: str, stream_url: str) -> MindraExecutionResult:
        absolute_url = stream_url if stream_url.startswith("http") else f"{self.base_url}{stream_url}"
        chunks: list[str] = []
        tool_events: list[dict] = []
        approvals: list[MindraApproval] = []
        final_status = "running"
        final_answer: str | None = None
        event_name: str | None = None
        data_lines: list[str] = []

        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("GET", absolute_url, headers={"x-api-key": self.api_key}) as response:
                response.raise_for_status()
                for raw_line in response.iter_lines():
                    line = raw_line.strip() if raw_line else ""
                    if not line:
                        if event_name and data_lines:
                            payload = json.loads("\n".join(data_lines))
                            if event_name == "chunk":
                                chunks.append(payload.get("content", ""))
                            elif event_name in {"tool_executing", "tool_result"}:
                                tool_events.append({"event": event_name, "payload": payload})
                            elif event_name == "approval_request":
                                approvals.append(
                                    MindraApproval(
                                        approval_id=payload["approval_id"],
                                        tool_name=payload.get("tool_name"),
                                        tool_input=payload.get("tool_input"),
                                    )
                                )
                            elif event_name == "done":
                                final_status = payload.get("status", "completed")
                                final_answer = payload.get("final_answer")
                        event_name = None
                        data_lines = []
                        continue

                    if line.startswith("event: "):
                        event_name = line[7:]
                    elif line.startswith("data: "):
                        data_lines.append(line[6:])

        if event_name and data_lines:
            payload = json.loads("\n".join(data_lines))
            if event_name == "done":
                final_status = payload.get("status", "completed")
                final_answer = payload.get("final_answer")

        if final_status == "running":
            raise RuntimeError(f"Mindra stream ended without done event for execution {execution_id}")
        return MindraExecutionResult(
            execution_id=execution_id,
            stream_url=stream_url,
            status=final_status,
            final_answer=final_answer,
            chunks=chunks,
            tool_events=tool_events,
            approvals=approvals,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
