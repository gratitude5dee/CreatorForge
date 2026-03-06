"""A2A agent-card builder for CreatorForge."""

from __future__ import annotations

import json
from datetime import datetime, timezone

try:
    from payments_py.a2a.agent_card import build_payment_agent_card
    _HAS_A2A = True
except ImportError:  # pragma: no cover
    build_payment_agent_card = None  # type: ignore[assignment]
    _HAS_A2A = False

from ..pricing.policy import BASE_CREDITS


def build_creatorforge_agent_card(
    base_url: str,
    plan_id: str,
    agent_id: str,
    sponsored_slots: dict | None = None,
) -> dict:
    if not _HAS_A2A:
        raise RuntimeError("payments-py a2a extras are required")
    skills = [
        {
            "id": f"creatorforge_{name.replace('-', '_')}",
            "name": name,
            "description": f"CreatorForge {name} service",
            "tags": ["creatorforge", "creative", "paid"],
        }
        for name in BASE_CREDITS
    ]

    cost_description = "Credits vary by service: " + ", ".join(
        [f"{name}={credits}" for name, credits in BASE_CREDITS.items()]
    )
    base_card = {
        "name": "CreatorForge Agent",
        "description": "Autonomous creative asset economy seller",
        "url": base_url.rstrip("/"),
        "version": "1.0.0",
        "skills": skills,
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "sponsoredSlots": sponsored_slots or {},
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        },
    }
    return build_payment_agent_card(
        base_card,
        {
            "paymentType": "dynamic",
            "credits": min(BASE_CREDITS.values()),
            "planId": plan_id,
            "agentId": agent_id,
            "costDescription": cost_description,
        },
    )


def main() -> None:
    import os

    base_url = os.getenv("NVM_BASE_URL", "http://localhost:3010")
    plan_id = os.environ["NVM_PLAN_ID"]
    agent_id = os.environ["NVM_AGENT_ID"]
    print(json.dumps(build_creatorforge_agent_card(base_url, plan_id, agent_id), indent=2))
