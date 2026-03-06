"""Seller-facing CreatorForge APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request

from .models import CreativeAssetRequest, CreativeAssetResponse, ServiceName
from ..payments.a2a_server import build_creatorforge_agent_card

router = APIRouter(tags=["seller"])


def _is_peak_demand() -> bool:
    hour = datetime.utcnow().hour
    return 0 <= hour <= 2  # simple deterministic window for surge pricing demo


async def _handle_service(service: ServiceName, req: CreativeAssetRequest, request: Request) -> CreativeAssetResponse:
    c = request.app.state.container
    trace_id = str(uuid4())

    repeat_buyer = c.repo.buyer_sale_count(req.buyer_id) > 0
    quote = c.pricing.quote(
        service=service,
        buyer_id=req.buyer_id,
        repeat_buyer=repeat_buyer,
        peak_demand=_is_peak_demand(),
    )

    verification = await c.x402.require_and_verify(request=request, endpoint=request.url.path)
    c.repo.record_audit_event(trace_id, "ceo", "request_received", {"service": service, "buyer": req.buyer_id})

    campaign_id = c.repo.create_campaign(
        trace_id=trace_id,
        service=service,
        buyer_id=req.buyer_id,
        brief=req.brief,
    )

    content, quality, ad_context = c.ceo.generate_asset(service, req, trace_id)
    if service == "ad-enriched" and not ad_context:
        raise HTTPException(status_code=502, detail="ad-enriched service requires ZeroClick context")

    asset_id = c.repo.create_creative_asset(
        campaign_id=campaign_id,
        trace_id=trace_id,
        service=service,
        content=content,
        quality=quality,
        ad_context=ad_context,
    )

    settlement = await c.x402.settle(
        token=verification["token"],
        endpoint=request.url.path,
        agent_request_id=verification.get("agent_request_id"),
    )

    c.repo.record_sale(
        trace_id=trace_id,
        buyer_id=req.buyer_id,
        service=service,
        credits=quote.settlement_credits,
        settlement=settlement,
    )
    c.repo.record_budget_entry(
        trace_id=trace_id,
        vendor_id=req.buyer_id,
        credits=quote.settlement_credits,
        direction="sell",
        note=f"sold {service}",
    )
    c.repo.record_audit_event(trace_id, "quality-auditor", "quality_scored", quality)

    if ad_context:
        c.repo.record_ad_event(trace_id, "included", "zeroclick", ad_context)

    return CreativeAssetResponse(
        asset_id=asset_id,
        trace_id=trace_id,
        service=service,
        content=content,
        quote=quote,
        quality=quality,
        settlement=settlement,
        ad_context=ad_context,
    )


@router.post("/v1/assets/ad-copy", response_model=CreativeAssetResponse)
async def create_ad_copy(req: CreativeAssetRequest, request: Request):
    return await _handle_service("ad-copy", req, request)


@router.post("/v1/assets/visual", response_model=CreativeAssetResponse)
async def create_visual(req: CreativeAssetRequest, request: Request):
    return await _handle_service("visual", req, request)


@router.post("/v1/assets/brand-kit", response_model=CreativeAssetResponse)
async def create_brand_kit(req: CreativeAssetRequest, request: Request):
    return await _handle_service("brand-kit", req, request)


@router.post("/v1/assets/campaign", response_model=CreativeAssetResponse)
async def create_campaign(req: CreativeAssetRequest, request: Request):
    return await _handle_service("campaign", req, request)


@router.post("/v1/assets/ad-enriched", response_model=CreativeAssetResponse)
async def create_ad_enriched(req: CreativeAssetRequest, request: Request):
    return await _handle_service("ad-enriched", req, request)


@router.get("/pricing")
async def pricing(request: Request, buyer_id: str = Query(default="anonymous")):
    c = request.app.state.container
    repeat_buyer = c.repo.buyer_sale_count(buyer_id) > 0
    slots = c.zeroclick.fetch_marketplace_slots("creative-assets")
    tiers = {
        name: c.pricing.quote(name, buyer_id=buyer_id, repeat_buyer=repeat_buyer, peak_demand=_is_peak_demand()).model_dump()
        for name in ["ad-copy", "visual", "brand-kit", "campaign", "ad-enriched"]
    }
    return {
        "buyer_id": buyer_id,
        "tiers": tiers,
        "sponsored_slots": slots,
    }


@router.get("/.well-known/agent.json")
async def agent_card(request: Request):
    c = request.app.state.container
    slots = c.zeroclick.fetch_marketplace_slots("creative-assets")
    return build_creatorforge_agent_card(
        base_url=c.settings.nvm_base_url,
        plan_id=c.settings.nvm_plan_id,
        agent_id=c.settings.nvm_agent_id,
        sponsored_slots=slots,
    )


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/stats")
async def stats(request: Request):
    return request.app.state.container.repo.get_stats()
