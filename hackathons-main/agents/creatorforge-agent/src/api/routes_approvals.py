"""Human approval workflow routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request

from .models import ApprovalDecision, ApprovalRequest

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])


@router.get("/pending", response_model=list[ApprovalRequest])
async def pending(request: Request):
    rows = request.app.state.container.repo.list_pending_approvals()
    result = []
    for row in rows:
        result.append(
            ApprovalRequest(
                approval_id=row["id"],
                trace_id=row["trace_id"],
                vendor_id=row["vendor_id"],
                credits=row["credits"],
                status=row["status"],
                reason=row["reason"],
                requested_at=datetime.fromisoformat(row["created_at"]),
            )
        )
    return result


@router.post("/{approval_id}/decision")
async def decide(approval_id: int, decision: ApprovalDecision, request: Request):
    repo = request.app.state.container.repo
    current = repo.get_approval(approval_id)
    if not current:
        raise HTTPException(status_code=404, detail="approval not found")
    if current["status"] != "pending":
        raise HTTPException(status_code=409, detail="approval already resolved")

    repo.resolve_approval(
        approval_id=approval_id,
        approved=decision.approved,
        reviewer=decision.reviewer,
        note=decision.note,
    )
    repo.record_audit_event(
        current["trace_id"],
        "human-approval",
        "approval_decision",
        {"approval_id": approval_id, "approved": decision.approved, "reviewer": decision.reviewer},
    )
    return {"approval_id": approval_id, "status": "approved" if decision.approved else "rejected"}
