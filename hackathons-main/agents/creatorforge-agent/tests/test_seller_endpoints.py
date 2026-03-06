from dataclasses import dataclass
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.routes_seller as routes_seller
from src.api.routes_seller import router as seller_router
from src.payments.http_x402 import PaymentMiddlewareCompat, PaymentSettlementCaptureMiddleware
from src.pricing.policy import PricingPolicy
from src.storage.db import Database
from src.storage.repository import Repository


class FakeAuditor:
    def __init__(self, pass_gate: bool = True):
        self.pass_gate = pass_gate

    def gate(self, content: dict):
        quality = {"quality_score": 8.0, "compliance_score": 8.0, "status": "pass" if self.pass_gate else "review"}
        return self.pass_gate, quality, None if self.pass_gate else "rejected by quality gate"


@dataclass(frozen=True)
class FakeGenerationResult:
    content: dict
    quality: dict
    ad_context: dict | None
    mindra_execution_id: str
    mindra_status: str


class FakeCEO:
    def __init__(self, ad_context: dict | None = None, pass_gate: bool = True):
        self._ad_context = ad_context
        self.creative_director = SimpleNamespace(
            auditor=FakeAuditor(pass_gate=pass_gate),
            ad_agent=SimpleNamespace(track_callback=lambda trace_id, event, payload: None),
        )

    def generate_asset(self, service, req, trace_id):
        return FakeGenerationResult(
            content={"service": service, "body": "ok", "brief": req.brief},
            quality={"quality_score": 8.0, "compliance_score": 8.0, "status": "pass"},
            ad_context=self._ad_context if service == "ad-enriched" else None,
            mindra_execution_id="exec-1",
            mindra_status="completed",
        )


class FakeZeroClick:
    def fetch_marketplace_slots(self, category):
        return {"category": category, "slots": [{"id": "slot-1"}]}


@dataclass
class FakeSettings:
    nvm_base_url: str = "http://localhost:3010"
    nvm_plan_id: str = "plan-test"
    nvm_agent_id: str = "agent-test"


@dataclass
class FakeContainer:
    settings: FakeSettings
    repo: Repository
    pricing: PricingPolicy
    ceo: FakeCEO
    zeroclick: FakeZeroClick
    mindra: object


def make_app(tmp_path, ad_context=None, pass_gate=True) -> FastAPI:
    db = Database(str(tmp_path / "creatorforge-test.db"))
    db.initialize()
    repo = Repository(db)
    pricing = PricingPolicy()

    app = FastAPI()
    app.state.container = FakeContainer(
        settings=FakeSettings(),
        repo=repo,
        pricing=pricing,
        ceo=FakeCEO(ad_context=ad_context, pass_gate=pass_gate),
        zeroclick=FakeZeroClick(),
        mindra=SimpleNamespace(),
    )
    app.add_middleware(
        PaymentMiddlewareCompat,
        payments=None,
        routes={
            f"POST {path}": {
                "plan_id": "plan-test",
                "credits": (lambda service: (lambda req: pricing.quote_from_payload(
                    service,
                    req.body,
                    repo.buyer_sale_count(str(req.body.get("buyer_id", "anonymous"))) > 0,
                ).settlement_credits))(service),
            }
            for path, service in {
                "/v1/assets/ad-copy": "ad-copy",
                "/v1/assets/visual": "visual",
                "/v1/assets/brand-kit": "brand-kit",
                "/v1/assets/campaign": "campaign",
                "/v1/assets/ad-enriched": "ad-enriched",
            }.items()
        },
    )
    app.add_middleware(PaymentSettlementCaptureMiddleware, repo=repo)
    app.include_router(seller_router)
    return app


def test_paid_endpoints_require_402_then_succeed(tmp_path, monkeypatch):
    monkeypatch.setattr(routes_seller, "build_creatorforge_agent_card", lambda **kwargs: {"agent": "creatorforge", **kwargs})
    client = TestClient(make_app(tmp_path, ad_context={"ad": "context"}))

    endpoints = {
        "/v1/assets/ad-copy": "ad-copy",
        "/v1/assets/visual": "visual",
        "/v1/assets/brand-kit": "brand-kit",
        "/v1/assets/campaign": "campaign",
        "/v1/assets/ad-enriched": "ad-enriched",
    }
    for path, service in endpoints.items():
        first = client.post(path, json={"brief": "Launch a fitness app", "buyer_id": f"{service}-buyer"})
        assert first.status_code == 402
        assert "payment-required" in first.headers

        second = client.post(
            path,
            headers={"payment-signature": "token"},
            json={"brief": "Launch a fitness app", "buyer_id": f"{service}-buyer"},
        )
        assert second.status_code == 200
        body = second.json()
        assert body["service"] == service
        assert body["settlement"]["credits_redeemed"] == body["quote"]["settlement_credits"]


def test_quality_gate_blocks_delivery(tmp_path):
    client = TestClient(make_app(tmp_path, pass_gate=False))
    resp = client.post(
        "/v1/assets/ad-copy",
        headers={"payment-signature": "token"},
        json={"brief": "Launch a fitness app", "buyer_id": "buyer-1"},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["campaign_status"] == "rejected"
    assert "payment-response" not in resp.headers


def test_agent_card_and_pricing_include_sponsored_slots(tmp_path, monkeypatch):
    monkeypatch.setattr(routes_seller, "build_creatorforge_agent_card", lambda **kwargs: {"agent": "creatorforge", **kwargs})
    client = TestClient(make_app(tmp_path))

    pricing = client.get("/pricing", params={"buyer_id": "buyer-1"})
    assert pricing.status_code == 200
    assert pricing.json()["sponsored_slots"]["category"] == "creative-assets"

    agent = client.get("/.well-known/agent.json")
    assert agent.status_code == 200
    assert agent.json()["agent"] == "creatorforge"
