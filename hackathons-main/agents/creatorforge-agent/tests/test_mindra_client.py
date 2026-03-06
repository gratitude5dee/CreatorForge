from src.orchestration.mindra_client import MindraClient


class FakeRunResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "execution_id": "exec-123",
            "stream_url": "/api/v1/workflows/execute/exec-123/stream",
            "status": "running",
        }


class FakeStreamResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        return None

    def iter_lines(self):
        return iter(
            [
                "event: chunk",
                'data: {"content":"hello"}',
                "",
                "event: approval_request",
                'data: {"approval_id":"apr-1","tool_name":"send_email","tool_input":{"to":"x@y.z"}}',
                "",
                "event: done",
                'data: {"execution_id":"exec-123","status":"completed","final_answer":"ok"}',
            ]
        )


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, headers=None, json=None):
        self.calls.append(("POST", url, headers, json))
        if "/approve/" in url or "/reject/" in url:
            return FakeDecisionResponse(url, json)
        return FakeRunResponse()

    def stream(self, method, url, headers=None):
        self.calls.append((method, url, headers, None))
        return FakeStreamResponse()


class FakeDecisionResponse:
    def __init__(self, url, payload):
        self.url = url
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return {"url": self.url, "payload": self.payload, "status": "ok"}


def test_mindra_workflow_run_and_stream(monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr("src.orchestration.mindra_client.httpx.Client", lambda *args, **kwargs: fake_client)

    client = MindraClient(
        base_url="https://api.mindra.co",
        api_key="mindra-key",
        creative_workflow_slug="creative-slug",
        procurement_workflow_slug="procurement-slug",
        connect_timeout_seconds=10,
        read_timeout_seconds=30,
    )
    result = client.run_creative_workflow("trace-1", {"service": "ad-copy"})

    assert result.execution_id == "exec-123"
    assert result.status == "completed"
    assert result.final_answer == "ok"
    assert result.approvals[0].approval_id == "apr-1"


def test_mindra_approve_and_reject(monkeypatch):
    fake_client = FakeClient()
    monkeypatch.setattr("src.orchestration.mindra_client.httpx.Client", lambda *args, **kwargs: fake_client)

    client = MindraClient(
        base_url="https://api.mindra.co",
        api_key="mindra-key",
        creative_workflow_slug="creative-slug",
        procurement_workflow_slug="procurement-slug",
        connect_timeout_seconds=10,
        read_timeout_seconds=30,
    )

    approved = client.approve_execution("exec-1", "apr-1", "looks good")
    rejected = client.reject_execution("exec-1", "apr-2", "declined")

    assert approved["status"] == "ok"
    assert "/approve/apr-1" in approved["url"]
    assert approved["payload"] == {"reason": "looks good"}
    assert rejected["status"] == "ok"
    assert "/reject/apr-2" in rejected["url"]
    assert rejected["payload"] == {"reason": "declined"}
