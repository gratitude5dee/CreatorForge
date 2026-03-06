"""Procurement orchestration routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from .models import ProcurementRunRequest, ProcurementRunResponse

router = APIRouter(prefix="/v1/procurement", tags=["procurement"])


@router.post("/run", response_model=ProcurementRunResponse)
async def run_procurement(req: ProcurementRunRequest, request: Request):
    trace_id = req.trace_id or str(uuid4())
    c = request.app.state.container

    decisions, pending = c.ceo.run_procurement(trace_id, req)
    c.repo.record_audit_event(
        trace_id,
        "procurement-director",
        "procurement_run",
        {"decisions": [d.model_dump() for d in decisions], "pending": pending},
    )

    return ProcurementRunResponse(trace_id=trace_id, decisions=decisions, pending_approvals=pending)


@router.get("/vendors")
async def vendors(request: Request):
    return {"vendors": request.app.state.container.repo.list_vendor_profiles()}


@router.get("/decisions/{decision_id}")
async def decision(decision_id: int, request: Request):
    row = request.app.state.container.repo.get_procurement_decision(decision_id)
    if not row:
        raise HTTPException(status_code=404, detail="decision not found")
    return row
