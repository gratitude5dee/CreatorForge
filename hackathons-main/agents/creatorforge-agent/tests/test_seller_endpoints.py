from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes_seller import router as seller_router
from src.pricing.policy import PricingPolicy


class FakeRepo:
    def __init__(self):
        self.sales = 0

    def buyer_sale_count(self, buyer_id: str) -> int:
        return 1 if buyer_id == "repeat" else 0

    def create_campaign(self, **kwargs):
        return 1

    def create_creative_asset(self, **kwargs):
        return 42

    def record_sale(self, **kwargs):
        self.sales += 1

    def record_budget_entry(self, **kwargs):
        pass

    def record_audit_event(self, *args, **kwargs):
        pass

    def record_ad_event(self, *args, **kwargs):
        pass

    def get_stats(self):
        return {"sales_count": self.sales}


class FakeCEO:
    def generate_asset(self, service, req, trace_id):
        return ({"service": service, "body": "ok"}, {"quality_score": 8.0, "compliance_score": 8.0}, None)


class FakeX402:
    async def require_and_verify(self, request, endpoint):
        return {"token": "token", "agent_request_id": "req-1"}

    async def settle(self, token, endpoint, agent_request_id=None):
        return {
            "success": True,
            "payer": "buyer",
            "credits_redeemed": 1,
            "remaining_balance": 99,
            "tx_hash": "0xabc",
        }


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
    repo: FakeRepo
    pricing: PricingPolicy
    ceo: FakeCEO
    x402: FakeX402
    zeroclick: FakeZeroClick


def make_app() -> FastAPI:
    app = FastAPI()
    app.state.container = FakeContainer(
        settings=FakeSettings(),
        repo=FakeRepo(),
        pricing=PricingPolicy(),
        ceo=FakeCEO(),
        x402=FakeX402(),
        zeroclick=FakeZeroClick(),
    )
    app.include_router(seller_router)
    return app


def test_ad_copy_endpoint_success():
    client = TestClient(make_app())
    resp = client.post(
        "/v1/assets/ad-copy",
        json={"brief": "Launch a fitness app campaign", "buyer_id": "new", "channels": ["x"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "ad-copy"
    assert body["asset_id"] == 42


def test_pricing_endpoint_includes_sponsored_slots():
    client = TestClient(make_app())
    resp = client.get("/pricing", params={"buyer_id": "repeat"})
    assert resp.status_code == 200
    body = resp.json()
    assert "tiers" in body
    assert "sponsored_slots" in body
    assert body["sponsored_slots"]["category"] == "creative-assets"


def test_stats_endpoint():
    client = TestClient(make_app())
    resp = client.get("/stats")
    assert resp.status_code == 200
    assert resp.json()["sales_count"] == 0
