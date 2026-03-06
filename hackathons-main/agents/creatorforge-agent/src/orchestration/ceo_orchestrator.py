"""CEO orchestrator for the CreatorForge hierarchy."""

from __future__ import annotations

from ..api.models import CreativeAssetRequest, ProcurementRunRequest, ServiceName
from ..orchestration.creative_director import CreativeDirector
from ..orchestration.mindra_client import MindraClient
from ..orchestration.procurement_director import ProcurementDirector


class CEOOrchestrator:
    """Top-level orchestrator coordinating Creative and Procurement directors."""

    def __init__(
        self,
        creative_director: CreativeDirector,
        procurement_director: ProcurementDirector,
        mindra_client: MindraClient,
    ):
        self.creative_director = creative_director
        self.procurement_director = procurement_director
        self.mindra = mindra_client

    def generate_asset(self, service: ServiceName, req: CreativeAssetRequest, trace_id: str) -> tuple[dict, dict, dict | None]:
        dag = {
            "l0": ["ceo"],
            "l1": ["creative-director", "procurement-director"],
            "l2": ["copywriter", "designer", "brand-strategist", "quality-auditor", "ad-revenue"],
            "flow": ["ceo->creative-director", "creative-director->specialists", "specialists->quality-auditor"],
        }
        self.mindra.orchestrate(
            trace_id=trace_id,
            dag=dag,
            context={"service": service, "brief": req.brief, "audience": req.audience},
        )
        return self.creative_director.produce(service, req, trace_id)

    def run_procurement(self, trace_id: str, req: ProcurementRunRequest):
        dag = {
            "l0": ["ceo"],
            "l1": ["procurement-director"],
            "l2": ["market-scout", "quality-auditor"],
            "flow": ["ceo->procurement-director", "procurement-director->market-scout"],
        }
        self.mindra.orchestrate(
            trace_id=trace_id,
            dag=dag,
            context={"objective": req.objective, "vendor_count": len(req.vendors)},
        )
        return self.procurement_director.run(trace_id, req)
