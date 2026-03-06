"""Creative director orchestration of specialist creative agents."""

from __future__ import annotations

from ..agents.ad_revenue_agent import AdRevenueAgent
from ..agents.brand_strategist import BrandStrategistAgent
from ..agents.copywriter import CopywriterAgent
from ..agents.designer import DesignerAgent
from ..agents.quality_auditor import QualityAuditorAgent
from ..api.models import CreativeAssetRequest, ServiceName


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

    def produce(self, service: ServiceName, req: CreativeAssetRequest, trace_id: str) -> tuple[dict, dict, dict | None]:
        content: dict = {}
        ad_context: dict | None = None

        if service in ("ad-copy", "campaign", "ad-enriched"):
            content.update(self.copywriter.run(req.brief, req.brand, req.audience))

        if service in ("visual", "campaign"):
            content.update(self.designer.run(req.brief, req.brand, req.audience))

        if service in ("brand-kit", "campaign"):
            content.update(self.strategist.run(req.brief, req.brand, req.audience))

        if service == "ad-enriched":
            ad_payload, ad_context = self.ad_agent.enrich(req.brief, req.audience, trace_id)
            content.update(ad_payload)

        quality = self.auditor.run(content)
        return content, quality, ad_context
