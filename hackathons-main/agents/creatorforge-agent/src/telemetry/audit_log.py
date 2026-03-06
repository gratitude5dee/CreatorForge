"""Audit logging helpers."""

from __future__ import annotations

from ..storage.repository import Repository


def record_audit(repo: Repository, trace_id: str, agent_name: str, action: str, payload: dict) -> int:
    """Persist an immutable audit event."""
    return repo.record_audit_event(trace_id=trace_id, agent_name=agent_name, action=action, payload=payload)
