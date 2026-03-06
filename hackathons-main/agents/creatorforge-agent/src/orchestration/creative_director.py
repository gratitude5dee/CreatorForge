"""Creative director orchestration of specialist creative agents."""

from __future__ import annotations

from typing import TypedDict

from ..agents.ad_revenue_agent import AdRevenueAgent
from ..agents.brand_strategist import BrandStrategistAgent
from ..agents.copywriter import CopywriterAgent
from ..agents.designer import DesignerAgent
from ..agents.quality_auditor import QualityAuditorAgent
from ..api.models import CreativeAssetRequest, ServiceName

try:  # pragma: no cover - depends on langgraph runtime
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - local fallback
    END = START = StateGraph = None


class CreativeState(TypedDict, total=False):
    service: ServiceName
    req: CreativeAssetRequest
    trace_id: str
    content: dict
    quality: dict
    ad_context: dict | None


class CreativeDirector:
    def __init__(
        self,
        copywriter: CopywriterAgent,
        designer: DesignerAgent,
        strategist: BrandStrategistAgent,
        auditor: QualityAuditorAgent,
        ad_agent: AdRevenueAgent,
    ):
        self.copywriter = copywriter
        self.designer = designer
        self.strategist = strategist
        self.auditor = auditor
        self.ad_agent = ad_agent
        self._graph = self._build_graph()

    def produce(self, service: ServiceName, req: CreativeAssetRequest, trace_id: str) -> tuple[dict, dict, dict | None]:
        if self._graph is None:
            return self._run_fallback(service, req, trace_id)
        state = self._graph.invoke(
            {
                "service": service,
                "req": req,
                "trace_id": trace_id,
                "content": {},
                "quality": {},
                "ad_context": None,
            }
        )
        return state["content"], state["quality"], state.get("ad_context")

    def _run_fallback(self, service: ServiceName, req: CreativeAssetRequest, trace_id: str) -> tuple[dict, dict, dict | None]:
        state: CreativeState = {"service": service, "req": req, "trace_id": trace_id, "content": {}}
        state.update(self._maybe_enrich(state))
        state.update(self._copy_node(state))
        state.update(self._designer_node(state))
        state.update(self._brand_node(state))
        state.update(self._quality_node(state))
        return state["content"], state["quality"], state.get("ad_context")

    def _build_graph(self):
        if StateGraph is None:
            return None
        graph = StateGraph(CreativeState)
        graph.add_node("maybe_enrich", self._maybe_enrich)
        graph.add_node("copywriter", self._copy_node)
        graph.add_node("designer", self._designer_node)
        graph.add_node("brand", self._brand_node)
        graph.add_node("quality", self._quality_node)
        graph.add_edge(START, "maybe_enrich")
        graph.add_edge("maybe_enrich", "copywriter")
        graph.add_edge("copywriter", "designer")
        graph.add_edge("designer", "brand")
        graph.add_edge("brand", "quality")
        graph.add_edge("quality", END)
        return graph.compile()

    def _maybe_enrich(self, state: CreativeState) -> dict:
        if state["service"] != "ad-enriched":
            return {}
        ad_context = self.ad_agent.enrich(state["req"].brief, state["req"].audience, state["trace_id"])
        return {"ad_context": ad_context}

    def _copy_node(self, state: CreativeState) -> dict:
        if state["service"] not in ("ad-copy", "campaign", "ad-enriched"):
            return {}
        content = dict(state.get("content", {}))
        content.update(
            self.copywriter.run(
                state["req"].brief,
                state["req"].brand,
                state["req"].audience,
                state.get("ad_context"),
            )
        )
        if state["service"] == "ad-enriched" and state.get("ad_context"):
            content["sponsored_context"] = state["ad_context"]
            content["placement"] = "creative-output"
        return {"content": content}

    def _designer_node(self, state: CreativeState) -> dict:
        if state["service"] not in ("visual", "campaign"):
            return {}
        content = dict(state.get("content", {}))
        content.update(
            self.designer.run(
                state["req"].brief,
                state["req"].brand,
                state["req"].audience,
                state.get("ad_context"),
            )
        )
        return {"content": content}

    def _brand_node(self, state: CreativeState) -> dict:
        if state["service"] not in ("brand-kit", "campaign"):
            return {}
        content = dict(state.get("content", {}))
        content.update(
            self.strategist.run(
                state["req"].brief,
                state["req"].brand,
                state["req"].audience,
                state.get("ad_context"),
            )
        )
        return {"content": content}

    def _quality_node(self, state: CreativeState) -> dict:
        quality = self.auditor.run(state.get("content", {}))
        return {"quality": quality}
