"""FastAPI payment middleware compatibility helpers."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Callable

from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware


_FALLBACK_HEADERS = {
    "PAYMENT_REQUIRED": "payment-required",
    "PAYMENT_SIGNATURE": "payment-signature",
    "PAYMENT_RESPONSE": "payment-response",
}

try:  # pragma: no cover - depends on payments-py runtime
    from payments_py.x402.fastapi import PaymentMiddleware as _RealPaymentMiddleware
    from payments_py.x402.fastapi import X402_HEADERS as _PAYMENTS_HEADERS

    X402_HEADERS = dict(_PAYMENTS_HEADERS)
except ImportError:  # pragma: no cover - exercised in local tests without payments-py
    _RealPaymentMiddleware = None
    X402_HEADERS = dict(_FALLBACK_HEADERS)


@dataclass
class _FallbackPaymentRequest:
    body: dict[str, Any]
    headers: dict[str, str]
    method: str
    path: str


class _FallbackPaymentMiddleware(BaseHTTPMiddleware):
    """Minimal local fallback for tests when payments-py is unavailable."""

    def __init__(self, app, payments=None, routes: dict[str, dict] | None = None):
        super().__init__(app)
        self.routes = routes or {}

    async def dispatch(self, request, call_next):
        route_key = f"{request.method.upper()} {request.url.path}"
        config = self.routes.get(route_key)
        if not config:
            return await call_next(request)

        body = {}
        if request.method.upper() == "POST":
            raw_body = await request.body()
            if raw_body:
                body = json.loads(raw_body.decode("utf-8"))
            request._receive = _build_receive(raw_body)
        token = request.headers.get(X402_HEADERS["PAYMENT_SIGNATURE"], "").strip()
        credits = _resolve_credits(config["credits"], body, request)

        if not token:
            payment_required = {
                "planId": config["plan_id"],
                "endpoint": request.url.path,
                "credits": credits,
            }
            encoded = base64.b64encode(json.dumps(payment_required).encode("utf-8")).decode("utf-8")
            return JSONResponse(
                status_code=402,
                content={"detail": "Payment Required"},
                headers={X402_HEADERS["PAYMENT_REQUIRED"]: encoded},
            )

        response = await call_next(request)
        if response.status_code >= 400:
            return response

        settlement = {
            "success": True,
            "payer": "fallback-buyer",
            "credits_redeemed": credits,
            "remaining_balance": 100 - credits,
            "tx_hash": "fallback-tx",
        }
        encoded = base64.b64encode(json.dumps(settlement).encode("utf-8")).decode("utf-8")
        response.headers[X402_HEADERS["PAYMENT_RESPONSE"]] = encoded
        return response


class PaymentMiddlewareCompat:
    """Uses the real payments middleware when available, otherwise the local fallback."""

    def __new__(cls, app, payments=None, routes: dict[str, dict] | None = None):
        if _RealPaymentMiddleware is not None and payments is not None:
            return _RealPaymentMiddleware(app, payments=payments, routes=routes)
        return _FallbackPaymentMiddleware(app, payments=payments, routes=routes)


def _resolve_credits(credits: int | Callable[..., int], body: dict[str, Any], request) -> int:
    if callable(credits):
        ctx = _FallbackPaymentRequest(
            body=body,
            headers=dict(request.headers),
            method=request.method.upper(),
            path=request.url.path,
        )
        return int(credits(ctx))
    return int(credits)


def _build_receive(raw_body: bytes):
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": raw_body, "more_body": False}

    return receive


def decode_payment_response(header_value: str | None) -> dict[str, Any]:
    if not header_value:
        return {}
    try:
        return json.loads(base64.b64decode(header_value).decode("utf-8"))
    except Exception:
        return {}


class PaymentSettlementCaptureMiddleware(BaseHTTPMiddleware):
    """Persists settlement metadata and injects it into seller responses."""

    def __init__(self, app, repo):
        super().__init__(app)
        self.repo = repo

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        sale_context = getattr(request.state, "sale_context", None)
        if response.status_code >= 400:
            _remove_header(response, X402_HEADERS["PAYMENT_RESPONSE"])
            return response
        if not sale_context:
            return response

        settlement = decode_payment_response(response.headers.get(X402_HEADERS["PAYMENT_RESPONSE"]))
        if not settlement:
            settlement = {
                "success": True,
                "payer": request.headers.get(X402_HEADERS["PAYMENT_SIGNATURE"]),
                "credits_redeemed": sale_context["credits"],
                "remaining_balance": None,
                "tx_hash": None,
            }

        self.repo.record_sale(
            trace_id=sale_context["trace_id"],
            buyer_id=sale_context["buyer_id"],
            service=sale_context["service"],
            credits=sale_context["credits"],
            settlement=settlement,
            idempotency_key=f"sale:{sale_context['trace_id']}",
        )
        self.repo.record_budget_entry(
            trace_id=sale_context["trace_id"],
            vendor_id=sale_context["buyer_id"],
            credits=sale_context["credits"],
            direction="sell",
            note=f"sold {sale_context['service']}",
        )
        self.repo.record_audit_event(
            sale_context["trace_id"],
            "nevermined",
            "payment_settled",
            settlement,
            idempotency_key=f"audit:sale-settled:{sale_context['trace_id']}",
        )

        if "application/json" not in response.headers.get("content-type", ""):
            return response

        body_bytes = await _read_response_body(response)
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            headers = dict(response.headers)
            headers.pop("content-length", None)
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )

        payload["settlement"] = settlement
        headers = dict(response.headers)
        headers.pop("content-length", None)
        return JSONResponse(
            content=payload,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )


async def _read_response_body(response) -> bytes:
    body = getattr(response, "body", None)
    if body is not None:
        return body
    chunks: list[bytes] = []
    async for chunk in response.body_iterator:
        chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode("utf-8"))
    return b"".join(chunks)


def _remove_header(response, name: str) -> None:
    if name in response.headers:
        del response.headers[name]
