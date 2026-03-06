"""Pydantic API models for CreatorForge."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ServiceName = Literal["ad-copy", "visual", "brand-kit", "campaign", "ad-enriched"]


class CreativeAssetRequest(BaseModel):
    brief: str = Field(..., min_length=3)
    brand: str | None = None
    audience: str | None = None
    channels: list[str] = Field(default_factory=list)
    buyer_id: str = Field(default="anonymous", min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PricingModifier(BaseModel):
    name: str
    delta_percent: float
    reason: str


class PricingQuote(BaseModel):
    service: ServiceName
    buyer_id: str
    base_credits: int
    effective_credits: float
    settlement_credits: int
    modifiers: list[PricingModifier] = Field(default_factory=list)
    generated_at: datetime


class CreativeAssetResponse(BaseModel):
    asset_id: int
    trace_id: str
    service: ServiceName
    content: dict[str, Any]
    quote: PricingQuote
    quality: dict[str, Any]
    settlement: dict[str, Any]
    ad_context: dict[str, Any] | None = None
    campaign_status: Literal["delivered"] = "delivered"


class QualityGateFailure(BaseModel):
    trace_id: str
    campaign_id: int
    service: ServiceName
    quality: dict[str, Any]
    reason: str
    campaign_status: Literal["rejected"] = "rejected"


class VendorCandidate(BaseModel):
    vendor_id: str
    vendor_name: str
    endpoint: str
    plan_id: str
    agent_id: str
    expected_credits: int = Field(default=1, ge=1)
    query: str


class ProcurementRunRequest(BaseModel):
    objective: str
    trace_id: str | None = None
    vendors: list[VendorCandidate] = Field(..., min_length=1)
    auto_approve: bool = False


class VendorScore(BaseModel):
    vendor_id: str
    quality: float
    compliance: float
    latency_score: float
    cost_efficiency: float
    roi_score: float


class ProcurementDecision(BaseModel):
    decision_id: int
    trace_id: str
    selected_vendor_id: str
    action: Literal["repeat", "switch", "hold", "buy_new", "blocked", "pending_approval"]
    reason: str
    roi_score: float | None = None
    alternate_forecast: float | None = None
    approval_request_id: int | None = None
    mindra_execution_id: str | None = None
    mindra_approval_id: str | None = None


class ProcurementRunResponse(BaseModel):
    trace_id: str
    decisions: list[ProcurementDecision]
    pending_approvals: list[int] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    approval_id: int
    trace_id: str
    vendor_id: str
    credits: int
    status: Literal["pending", "approved", "rejected"]
    reason: str
    requested_at: datetime
    mindra_execution_id: str | None = None
    mindra_approval_id: str | None = None


class ApprovalDecision(BaseModel):
    approved: bool
    reviewer: str
    note: str | None = None
    reason: str | None = None


class AuditEvent(BaseModel):
    trace_id: str
    agent_name: str
    action: str
    payload: dict[str, Any]
    created_at: datetime


class PaymentEvent(BaseModel):
    trace_id: str
    direction: Literal["buy", "sell"]
    endpoint: str
    credits: int
    payer: str | None = None
    tx_hash: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class AdAttributionEvent(BaseModel):
    trace_id: str
    event: Literal["considered", "included", "clicked", "converted"]
    provider: str = "zeroclick"
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AdAttributionCallback(BaseModel):
    trace_id: str = Field(..., min_length=1)
    event: Literal["clicked", "converted"]
    payload: dict[str, Any] = Field(default_factory=dict)
    provider: str = "zeroclick"
