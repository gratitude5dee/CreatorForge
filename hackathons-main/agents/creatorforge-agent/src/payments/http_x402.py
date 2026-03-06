"""HTTP x402 helper for FastAPI routes."""

from __future__ import annotations

import base64
import json

from fastapi import HTTPException, Request

from ..integrations.nevermined_client import NeverminedClient


class X402HttpService:
    """Handles x402 verification + settlement for API endpoints."""

    def __init__(self, nevermined: NeverminedClient):
        self.nevermined = nevermined

    async def require_and_verify(self, request: Request, endpoint: str) -> dict:
        token = request.headers.get("payment-signature", "").strip()
        payment_required = self.nevermined.build_payment_required(endpoint)
        payment_required_b64 = base64.b64encode(
            json.dumps(payment_required).encode("utf-8")
        ).decode("utf-8")

        if not token:
            raise HTTPException(
                status_code=402,
                detail="Payment Required",
                headers={"payment-required": payment_required_b64},
            )

        verify = await self.nevermined.verify_token(token=token, endpoint=endpoint)
        if not verify.success:
            raise HTTPException(
                status_code=402,
                detail=f"Payment verification failed: {verify.error}",
                headers={"payment-required": payment_required_b64},
            )

        return {
            "token": token,
            "payer": verify.payer,
            "agent_request_id": verify.agent_request_id,
        }

    async def settle(self, token: str, endpoint: str, agent_request_id: str | None = None) -> dict:
        settlement = await self.nevermined.settle_token(
            token=token,
            endpoint=endpoint,
            agent_request_id=agent_request_id,
        )
        if not settlement.success:
            raise HTTPException(status_code=502, detail=f"Settlement failed: {settlement.error}")

        return {
            "success": settlement.success,
            "payer": settlement.payer,
            "credits_redeemed": settlement.credits_redeemed,
            "remaining_balance": settlement.remaining_balance,
            "tx_hash": settlement.tx_hash,
        }
