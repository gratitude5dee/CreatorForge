"""Seller-facing CreatorForge APIs."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request

from .models import AdAttributionCallback, CreativeAssetRequest, CreativeAssetResponse, QualityGateFailure, ServiceName
from ..payments.a2a_server import build_creatorforge_agent_card

router = APIRouter(tags=["seller"])

async def _handle_service(service: ServiceName, req: CreativeAssetRequest, request: Request) -> CreativeAssetResponse:
    c = request.app.state.container
    trace_id = str(uuid4())

    repeat_buyer = c.repo.buyer_sale_count(req.buyer_id) > 0
    quote = c.pricing.quote(
        service=service,
        buyer_id=req.buyer_id,
        repeat_buyer=repeat_buyer,
        peak_demand=c.pricing._is_peak_window(),
    )

    c.repo.record_audit_event(
        trace_id,
        "ceo",
        "request_received",
        {"service": service, "buyer": req.buyer_id},
        idempotency_key=f"audit:request:{trace_id}",
    )

    campaign_id = c.repo.create_campaign(
        trace_id=trace_id,
        service=service,
        buyer_id=req.buyer_id,
        brief=req.brief,
    )
    c.repo.update_campaign_status(campaign_id, "generating")

    result = c.ceo.generate_asset(service, req, trace_id)
    if service == "ad-enriched" and not result.ad_context:
        c.repo.update_campaign_status(campaign_id, "rejected", "missing ZeroClick context")
        raise HTTPException(status_code=502, detail="ad-enriched service requires ZeroClick context")

    passed, quality, rejection_reason = c.ceo.creative_director.auditor.gate(result.content)
    if not passed:
        c.repo.update_campaign_status(campaign_id, "rejected", rejection_reason)
        c.repo.record_audit_event(
            trace_id,
            "quality-auditor",
            "quality_gate_rejected",
            {"reason": rejection_reason, "quality": quality},
            idempotency_key=f"audit:quality-rejected:{trace_id}",
        )
        raise HTTPException(
            status_code=422,
            detail=QualityGateFailure(
                trace_id=trace_id,
                campaign_id=campaign_id,
                service=service,
                quality=quality,
                reason=rejection_reason or "quality gate failed",
            ).model_dump(),
        )

    asset_id = c.repo.create_creative_asset(
        campaign_id=campaign_id,
        trace_id=trace_id,
        service=service,
        content=result.content,
        quality=quality,
        ad_context=result.ad_context,
        provenance={"mindra_execution_id": result.mindra_execution_id, "mindra_status": result.mindra_status},
    )
    if service == "ad-enriched" and result.ad_context:
        c.ceo.creative_director.ad_agent.mark_included(trace_id, result.ad_context)
    c.repo.update_campaign_status(campaign_id, "delivered")
    c.repo.record_audit_event(
        trace_id,
        "quality-auditor",
        "quality_scored",
        quality,
        idempotency_key=f"audit:quality:{trace_id}",
    )
    request.state.sale_context = {
        "trace_id": trace_id,
        "buyer_id": req.buyer_id,
        "service": service,
        "credits": quote.settlement_credits,
    }

    return CreativeAssetResponse(
        asset_id=asset_id,
        trace_id=trace_id,
        service=service,
        content=result.content,
        quote=quote,
        quality=quality,
        settlement={},
        ad_context=result.ad_context,
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
        name: c.pricing.quote(
            name,
            buyer_id=buyer_id,
            repeat_buyer=repeat_buyer,
            peak_demand=c.pricing._is_peak_window(),
        ).model_dump()
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


@router.post("/v1/ad-events/attribution")
async def attribution(event: AdAttributionCallback, request: Request):
    request.app.state.container.ceo.creative_director.ad_agent.track_callback(
        trace_id=event.trace_id,
        event=event.event,
        payload=event.payload,
    )
    return {"status": "recorded", "trace_id": event.trace_id, "event": event.event}
