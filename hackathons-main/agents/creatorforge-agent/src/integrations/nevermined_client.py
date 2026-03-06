"""Nevermined x402 client wrappers for verify/settle and buyer token creation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


try:
    from payments_py.payments import Payments
    from payments_py.common.types import PaymentOptions
    from payments_py.x402.helpers import build_payment_required
    _HAS_PAYMENTS = True
except ImportError:  # pragma: no cover - runtime dependency
    Payments = None  # type: ignore[assignment]
    PaymentOptions = None  # type: ignore[assignment]
    build_payment_required = None  # type: ignore[assignment]
    _HAS_PAYMENTS = False


_NETWORK_MAP = {
    "sandbox": "eip155:84532",
    "staging_sandbox": "eip155:84532",
    "live": "eip155:8453",
    "staging_live": "eip155:8453",
}


@dataclass(frozen=True)
class VerifyResult:
    success: bool
    payer: str | None
    agent_request_id: str | None
    error: str | None = None


@dataclass(frozen=True)
class SettleResult:
    success: bool
    payer: str | None
    credits_redeemed: int
    remaining_balance: int | None
    tx_hash: str | None
    error: str | None = None


class NeverminedClient:
    """Production wrapper around payments-py x402 operations."""

    def __init__(self, api_key: str, environment: str, plan_id: str, agent_id: str, base_url: str):
        if not _HAS_PAYMENTS:
            raise RuntimeError("payments-py must be installed for CreatorForge")
        self.plan_id = plan_id
        self.agent_id = agent_id
        self.environment = environment
        self.base_url = base_url.rstrip("/")
        self.network = _NETWORK_MAP.get(environment, "eip155:84532")
        self.payments = Payments.get_instance(
            PaymentOptions(nvm_api_key=api_key, environment=environment)
        )

    def build_payment_required(self, endpoint: str) -> dict:
        payload = build_payment_required(
            plan_id=self.plan_id,
            endpoint=f"{self.base_url}{endpoint}",
            agent_id=self.agent_id,
            http_verb="POST",
            network=self.network,
        )
        return payload.model_dump(by_alias=True)

    async def verify_token(self, token: str, endpoint: str) -> VerifyResult:
        payment_required = build_payment_required(
            plan_id=self.plan_id,
            endpoint=f"{self.base_url}{endpoint}",
            agent_id=self.agent_id,
            http_verb="POST",
            network=self.network,
        )
        result = await asyncio.to_thread(
            self.payments.facilitator.verify_permissions,
            payment_required,
            token,
        )
        return VerifyResult(
            success=bool(result.is_valid),
            payer=getattr(result, "payer", None),
            agent_request_id=getattr(result, "agent_request_id", None),
            error=getattr(result, "invalid_reason", None),
        )

    async def settle_token(self, token: str, endpoint: str, agent_request_id: str | None = None) -> SettleResult:
        payment_required = build_payment_required(
            plan_id=self.plan_id,
            endpoint=f"{self.base_url}{endpoint}",
            agent_id=self.agent_id,
            http_verb="POST",
            network=self.network,
        )

        result = await asyncio.to_thread(
            self.payments.facilitator.settle_permissions,
            payment_required,
            token,
            None,
            agent_request_id,
        )
        return SettleResult(
            success=bool(getattr(result, "success", False)),
            payer=getattr(result, "payer", None),
            credits_redeemed=int(getattr(result, "credits_redeemed", 0) or 0),
            remaining_balance=getattr(result, "remaining_balance", None),
            tx_hash=getattr(result, "transaction", None),
            error=getattr(result, "error_reason", None),
        )

    def get_access_token(self, plan_id: str, agent_id: str) -> str:
        token_result = self.payments.x402.get_x402_access_token(plan_id, agent_id)
        access_token = getattr(token_result, "access_token", None)
        if not access_token:
            raise RuntimeError("Nevermined did not return an x402 access token")
        return access_token
