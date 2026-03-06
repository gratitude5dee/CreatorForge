"""CEO orchestrator for the CreatorForge hierarchy."""

from __future__ import annotations

from dataclasses import dataclass

from ..api.models import CreativeAssetRequest, ProcurementRunRequest, ServiceName
from ..orchestration.creative_director import CreativeDirector
from ..orchestration.mindra_client import MindraClient
from ..orchestration.procurement_director import ProcurementDirector


@dataclass(frozen=True)
class AssetGenerationResult:
    content: dict
    quality: dict
    ad_context: dict | None
    mindra_execution_id: str
    mindra_status: str


@dataclass(frozen=True)
class ProcurementRunResult:
    decisions: list
    pending_approvals: list[int]
    mindra_execution_id: str
    mindra_status: str


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

    def generate_asset(self, service: ServiceName, req: CreativeAssetRequest, trace_id: str) -> AssetGenerationResult:
        execution = self.mindra.run_creative_workflow(
            trace_id=trace_id,
            context={"service": service, "brief": req.brief, "audience": req.audience},
        )
        content, quality, ad_context = self.creative_director.produce(service, req, trace_id)
        return AssetGenerationResult(
            content=content,
            quality=quality,
            ad_context=ad_context,
            mindra_execution_id=execution.execution_id,
            mindra_status=execution.status,
        )

    def run_procurement(self, trace_id: str, req: ProcurementRunRequest) -> ProcurementRunResult:
        execution = self.mindra.run_procurement_workflow(
            trace_id=trace_id,
            context={"objective": req.objective, "vendor_count": len(req.vendors)},
        )
        approval_id = execution.approvals[0].approval_id if execution.approvals else None
        decisions, pending_approvals = self.procurement_director.run(
            trace_id,
            req,
            mindra_execution_id=execution.execution_id,
            mindra_approval_id=approval_id,
        )
        return ProcurementRunResult(
            decisions=decisions,
            pending_approvals=pending_approvals,
            mindra_execution_id=execution.execution_id,
            mindra_status=execution.status,
        )
