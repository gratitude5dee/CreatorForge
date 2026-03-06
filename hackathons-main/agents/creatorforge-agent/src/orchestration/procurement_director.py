"""Procurement director orchestration for budgeted external buying."""

from __future__ import annotations

from typing import TypedDict

from ..api.models import ProcurementDecision, ProcurementRunRequest
from ..agents.market_scout import MarketScoutAgent
from ..procurement.budget_engine import BudgetEngine
from ..procurement.roi_engine import compute_roi, rolling_roi
from ..procurement.vendor_selector import VendorSelector, VendorState
from ..storage.repository import Repository

try:  # pragma: no cover - depends on langgraph runtime
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover
    END = START = StateGraph = None


class ProcurementState(TypedDict, total=False):
    trace_id: str
    req: ProcurementRunRequest
    mindra_execution_id: str | None
    mindra_approval_id: str | None
    selected_vendor: object
    current_vendor_state: VendorState | None
    candidate_states: list[VendorState]
    action: str
    reason: str
    roi_score: float | None
    alternate_forecast: float | None
    approval_request_id: int | None
    pending_approvals: list[int]
    decisions: list[ProcurementDecision]


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
        self._graph = self._build_graph()

    def run(
        self,
        trace_id: str,
        req: ProcurementRunRequest,
        mindra_execution_id: str | None = None,
        mindra_approval_id: str | None = None,
    ) -> tuple[list[ProcurementDecision], list[int]]:
        if self._graph is None:
            state = self._run_fallback(trace_id, req, mindra_execution_id, mindra_approval_id)
        else:
            state = self._graph.invoke(
                {
                    "trace_id": trace_id,
                    "req": req,
                    "mindra_execution_id": mindra_execution_id,
                    "mindra_approval_id": mindra_approval_id,
                    "pending_approvals": [],
                    "decisions": [],
                }
            )
        return state["decisions"], state["pending_approvals"]

    def _build_graph(self):
        if StateGraph is None:
            return None
        graph = StateGraph(ProcurementState)
        graph.add_node("select_vendor", self._select_vendor)
        graph.add_node("budget_gate", self._budget_gate)
        graph.add_node("purchase_vendor", self._purchase_vendor)
        graph.add_edge(START, "select_vendor")
        graph.add_edge("select_vendor", "budget_gate")
        graph.add_edge("budget_gate", "purchase_vendor")
        graph.add_edge("purchase_vendor", END)
        return graph.compile()

    def _run_fallback(
        self,
        trace_id: str,
        req: ProcurementRunRequest,
        mindra_execution_id: str | None,
        mindra_approval_id: str | None,
    ) -> ProcurementState:
        state: ProcurementState = {
            "trace_id": trace_id,
            "req": req,
            "mindra_execution_id": mindra_execution_id,
            "mindra_approval_id": mindra_approval_id,
            "pending_approvals": [],
            "decisions": [],
        }
        state.update(self._select_vendor(state))
        state.update(self._budget_gate(state))
        state.update(self._purchase_vendor(state))
        return state

    def _select_vendor(self, state: ProcurementState) -> dict:
        candidate_states = [self._build_vendor_state(v) for v in state["req"].vendors]
        current_vendor_state = self._current_vendor_state(state["req"], candidate_states)
        action, reason = self.selector.select(current_vendor_state, candidate_states, cap_ok=True)

        if action == "switch":
            selected_vendor_id = max(
                (c for c in candidate_states if not current_vendor_state or c.vendor_id != current_vendor_state.vendor_id),
                key=lambda c: c.forecast_roi,
            ).vendor_id
        elif current_vendor_state:
            selected_vendor_id = current_vendor_state.vendor_id
        else:
            selected_vendor_id = max(candidate_states, key=lambda c: c.forecast_roi).vendor_id

        selected_vendor = next(v for v in state["req"].vendors if v.vendor_id == selected_vendor_id)
        alternate_forecast = max(
            [c.forecast_roi for c in candidate_states if c.vendor_id != selected_vendor_id] + [0.0]
        )
        return {
            "selected_vendor": selected_vendor,
            "current_vendor_state": current_vendor_state,
            "candidate_states": candidate_states,
            "action": action,
            "reason": reason,
            "alternate_forecast": alternate_forecast,
        }

    def _budget_gate(self, state: ProcurementState) -> dict:
        vendor = state["selected_vendor"]
        daily_spend = self.repo.daily_spend()
        vendor_spend = self.repo.vendor_daily_spend(vendor.vendor_id)
        check = self.budget_engine.evaluate(vendor.expected_credits, daily_spend, vendor_spend)
        if not check.allowed:
            decision_id = self.repo.create_procurement_decision(
                trace_id=state["trace_id"],
                selected_vendor_id=vendor.vendor_id,
                action="blocked",
                reason=check.reason,
                roi_score=None,
                alternate_forecast=state["alternate_forecast"],
                approval_request_id=None,
                mindra_execution_id=state.get("mindra_execution_id"),
                mindra_approval_id=state.get("mindra_approval_id"),
            )
            return {
                "decisions": [
                    ProcurementDecision(
                        decision_id=decision_id,
                        trace_id=state["trace_id"],
                        selected_vendor_id=vendor.vendor_id,
                        action="blocked",
                        reason=check.reason,
                        alternate_forecast=state["alternate_forecast"],
                        mindra_execution_id=state.get("mindra_execution_id"),
                        mindra_approval_id=state.get("mindra_approval_id"),
                    )
                ]
            }

        if check.approval_required and not state["req"].auto_approve:
            approval_id = self.repo.create_approval_request(
                trace_id=state["trace_id"],
                vendor_id=vendor.vendor_id,
                credits=vendor.expected_credits,
                reason="purchase exceeds approval threshold",
                mindra_execution_id=state.get("mindra_execution_id"),
                mindra_approval_id=state.get("mindra_approval_id"),
            )
            decision_id = self.repo.create_procurement_decision(
                trace_id=state["trace_id"],
                selected_vendor_id=vendor.vendor_id,
                action="pending_approval",
                reason="awaiting human approval",
                roi_score=None,
                alternate_forecast=state["alternate_forecast"],
                approval_request_id=approval_id,
                mindra_execution_id=state.get("mindra_execution_id"),
                mindra_approval_id=state.get("mindra_approval_id"),
            )
            return {
                "pending_approvals": [approval_id],
                "approval_request_id": approval_id,
                "decisions": [
                    ProcurementDecision(
                        decision_id=decision_id,
                        trace_id=state["trace_id"],
                        selected_vendor_id=vendor.vendor_id,
                        action="pending_approval",
                        reason="awaiting human approval",
                        approval_request_id=approval_id,
                        alternate_forecast=state["alternate_forecast"],
                        mindra_execution_id=state.get("mindra_execution_id"),
                        mindra_approval_id=state.get("mindra_approval_id"),
                    )
                ],
            }

        return {}

    def _purchase_vendor(self, state: ProcurementState) -> dict:
        if state.get("decisions"):
            return {}

        vendor = state["selected_vendor"]
        body, credits_used = self.market_scout.purchase(vendor)
        quality, compliance, latency_score, cost_efficiency = self.market_scout.extract_scores(body, vendor.expected_credits)
        roi = compute_roi(quality, compliance, latency_score, cost_efficiency)
        previous_rois = self.repo.vendor_recent_rois(vendor.vendor_id)
        updated_rolling = rolling_roi(previous_rois + [roi], window=3)

        self.repo.record_purchase(
            trace_id=state["trace_id"],
            vendor_id=vendor.vendor_id,
            endpoint=vendor.endpoint,
            credits=credits_used,
            quality=quality,
            compliance=compliance,
            latency_score=latency_score,
            cost_efficiency=cost_efficiency,
            roi_score=roi,
            settlement=body,
            mindra_execution_id=state.get("mindra_execution_id"),
            idempotency_key=f"purchase:{state['trace_id']}:{vendor.vendor_id}",
        )
        self.repo.record_budget_entry(
            trace_id=state["trace_id"],
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

        decision_id = self.repo.create_procurement_decision(
            trace_id=state["trace_id"],
            selected_vendor_id=vendor.vendor_id,
            action=state["action"],
            reason=state["reason"],
            roi_score=roi,
            alternate_forecast=state["alternate_forecast"],
            approval_request_id=None,
            mindra_execution_id=state.get("mindra_execution_id"),
            mindra_approval_id=state.get("mindra_approval_id"),
        )
        return {
            "roi_score": roi,
            "decisions": [
                ProcurementDecision(
                    decision_id=decision_id,
                    trace_id=state["trace_id"],
                    selected_vendor_id=vendor.vendor_id,
                    action=state["action"],
                    reason=state["reason"],
                    roi_score=roi,
                    alternate_forecast=state["alternate_forecast"],
                    mindra_execution_id=state.get("mindra_execution_id"),
                    mindra_approval_id=state.get("mindra_approval_id"),
                )
            ],
        }

    def _build_vendor_state(self, vendor) -> VendorState:
        recent_rois = self.repo.vendor_recent_rois(vendor.vendor_id)
        profile = next((row for row in self.repo.list_vendor_profiles() if row["vendor_id"] == vendor.vendor_id), None)
        forecast = float(profile["rolling_roi"]) if profile else max(5.5, round(11.0 - vendor.expected_credits, 2))
        last_purchase = self.repo.vendor_last_purchase(vendor.vendor_id)
        return VendorState(
            vendor_id=vendor.vendor_id,
            rolling_roi=rolling_roi(recent_rois, window=3),
            forecast_roi=forecast,
            recent_samples=len(recent_rois),
            last_success=bool(last_purchase),
        )

    def _current_vendor_state(
        self,
        req: ProcurementRunRequest,
        candidate_states: list[VendorState],
    ) -> VendorState | None:
        candidate_by_vendor = {state.vendor_id: state for state in candidate_states}
        latest_vendor_id: str | None = None
        latest_purchase_id = -1
        for vendor in req.vendors:
            last_purchase = self.repo.vendor_last_purchase(vendor.vendor_id)
            if not last_purchase:
                continue
            purchase_id = int(last_purchase["id"])
            if purchase_id > latest_purchase_id:
                latest_purchase_id = purchase_id
                latest_vendor_id = vendor.vendor_id
        if latest_vendor_id is None:
            return None
        return candidate_by_vendor[latest_vendor_id]
