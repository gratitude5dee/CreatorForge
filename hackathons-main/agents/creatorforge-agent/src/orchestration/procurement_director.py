"""Procurement director orchestration for budgeted external buying."""

from __future__ import annotations

from ..api.models import ProcurementDecision, ProcurementRunRequest
from ..agents.market_scout import MarketScoutAgent
from ..procurement.budget_engine import BudgetEngine
from ..procurement.roi_engine import compute_roi, rolling_roi
from ..procurement.vendor_selector import VendorSelector, VendorState
from ..storage.repository import Repository


class ProcurementDirector:
    def __init__(
        self,
        market_scout: MarketScoutAgent,
        budget_engine: BudgetEngine,
        selector: VendorSelector,
        repo: Repository,
    ):
        self.market_scout = market_scout
        self.budget_engine = budget_engine
        self.selector = selector
        self.repo = repo

    def run(self, trace_id: str, req: ProcurementRunRequest) -> tuple[list[ProcurementDecision], list[int]]:
        decisions: list[ProcurementDecision] = []
        pending_approvals: list[int] = []

        vendor_profiles = {v["vendor_id"]: v for v in self.repo.list_vendor_profiles()}

        for vendor in req.vendors:
            daily_spend = self.repo.daily_spend()
            vendor_spend = self.repo.vendor_daily_spend(vendor.vendor_id)
            check = self.budget_engine.evaluate(vendor.expected_credits, daily_spend, vendor_spend)

            if not check.allowed:
                decision_id = self.repo.create_procurement_decision(
                    trace_id=trace_id,
                    selected_vendor_id=vendor.vendor_id,
                    action="blocked",
                    reason=check.reason,
                    roi_score=None,
                    alternate_forecast=None,
                    approval_request_id=None,
                )
                decisions.append(
                    ProcurementDecision(
                        decision_id=decision_id,
                        trace_id=trace_id,
                        selected_vendor_id=vendor.vendor_id,
                        action="blocked",
                        reason=check.reason,
                    )
                )
                continue

            if check.approval_required and not req.auto_approve:
                approval_id = self.repo.create_approval_request(
                    trace_id=trace_id,
                    vendor_id=vendor.vendor_id,
                    credits=vendor.expected_credits,
                    reason="purchase exceeds approval threshold",
                )
                pending_approvals.append(approval_id)
                decision_id = self.repo.create_procurement_decision(
                    trace_id=trace_id,
                    selected_vendor_id=vendor.vendor_id,
                    action="pending_approval",
                    reason="awaiting human approval",
                    roi_score=None,
                    alternate_forecast=None,
                    approval_request_id=approval_id,
                )
                decisions.append(
                    ProcurementDecision(
                        decision_id=decision_id,
                        trace_id=trace_id,
                        selected_vendor_id=vendor.vendor_id,
                        action="pending_approval",
                        reason="awaiting human approval",
                        approval_request_id=approval_id,
                    )
                )
                continue

            body, credits_used = self.market_scout.purchase(vendor)
            quality, compliance, latency_score, cost_efficiency = self.market_scout.extract_scores(
                body, vendor.expected_credits
            )
            roi = compute_roi(quality, compliance, latency_score, cost_efficiency)

            prev_rois = self.repo.vendor_recent_rois(vendor.vendor_id)
            updated_rolling = rolling_roi(prev_rois + [roi], window=3)

            self.repo.record_purchase(
                trace_id=trace_id,
                vendor_id=vendor.vendor_id,
                endpoint=vendor.endpoint,
                credits=credits_used,
                quality=quality,
                compliance=compliance,
                latency_score=latency_score,
                cost_efficiency=cost_efficiency,
                roi_score=roi,
                settlement=body,
            )
            self.repo.record_budget_entry(
                trace_id=trace_id,
                vendor_id=vendor.vendor_id,
                credits=credits_used,
                direction="buy",
                note="external procurement",
            )
            self.repo.upsert_vendor_profile(
                vendor_id=vendor.vendor_id,
                vendor_name=vendor.vendor_name,
                endpoint=vendor.endpoint,
                rolling_roi=updated_rolling,
                quality=quality,
                compliance=compliance,
                latency=latency_score,
                cost_efficiency=cost_efficiency,
            )

            alt_forecast = max(
                [float(v.get("rolling_roi", 0.0)) for k, v in vendor_profiles.items() if k != vendor.vendor_id] + [0.0]
            )

            current = VendorState(
                vendor_id=vendor.vendor_id,
                rolling_roi=rolling_roi(prev_rois, window=3),
                forecast_roi=rolling_roi(prev_rois, window=3),
                recent_samples=len(prev_rois),
                last_success=True,
            )
            candidates = [
                current,
                VendorState(
                    vendor_id=vendor.vendor_id,
                    rolling_roi=updated_rolling,
                    forecast_roi=updated_rolling,
                    recent_samples=len(prev_rois) + 1,
                    last_success=True,
                ),
            ]
            action, reason = self.selector.select(
                current=None if len(prev_rois) == 0 else current,
                candidates=candidates,
                cap_ok=True,
            )

            decision_id = self.repo.create_procurement_decision(
                trace_id=trace_id,
                selected_vendor_id=vendor.vendor_id,
                action=action,
                reason=reason,
                roi_score=roi,
                alternate_forecast=alt_forecast,
                approval_request_id=None,
            )
            decisions.append(
                ProcurementDecision(
                    decision_id=decision_id,
                    trace_id=trace_id,
                    selected_vendor_id=vendor.vendor_id,
                    action=action,
                    reason=reason,
                    roi_score=roi,
                    alternate_forecast=alt_forecast,
                )
            )

        return decisions, pending_approvals
