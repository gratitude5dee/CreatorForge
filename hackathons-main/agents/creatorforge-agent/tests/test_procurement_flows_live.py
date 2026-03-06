import os

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.models import ProcurementRunRequest, VendorCandidate
from src.orchestration.procurement_director import ProcurementDirector
from src.procurement.budget_engine import BudgetEngine
from src.procurement.vendor_selector import VendorSelector
from src.storage.db import Database
from src.storage.repository import Repository


class FakeMarketScout:
    def __init__(self, results: dict[str, dict]):
        self.results = results

    def purchase(self, vendor):
        body = self.results[vendor.vendor_id]
        return body, int(body.get("credits_used", vendor.expected_credits))

    def extract_scores(self, response_body: dict, expected_credits: int):
        quality = float(response_body.get("quality", 7.0))
        compliance = float(response_body.get("compliance", 7.0))
        latency_score = float(response_body.get("latency_score", 7.0))
        cost_efficiency = float(response_body.get("cost_efficiency", 7.0))
        return quality, compliance, latency_score, cost_efficiency


def _repo(tmp_path):
    db = Database(str(tmp_path / "procurement.db"))
    db.initialize()
    return Repository(db)


def test_procurement_repeat_and_switch_logic(tmp_path):
    repo = _repo(tmp_path)
    repo.upsert_vendor_profile("v1", "Vendor 1", "https://v1.test", 8.0, 8.0, 8.0, 8.0, 8.0)
    repo.upsert_vendor_profile("v2", "Vendor 2", "https://v2.test", 6.0, 6.0, 6.0, 6.0, 6.0)
    repo.record_purchase("t1", "v1", "https://v1.test", 2, 8, 8, 8, 8, 8.0, {}, idempotency_key="p1")
    repo.record_purchase("t2", "v1", "https://v1.test", 2, 8, 8, 8, 8, 8.0, {}, idempotency_key="p2")
    repo.record_purchase("t3", "v1", "https://v1.test", 2, 8, 8, 8, 8, 8.0, {}, idempotency_key="p3")

    director = ProcurementDirector(
        market_scout=FakeMarketScout(
            {"v1": {"quality": 8.0, "compliance": 8.0, "latency_score": 8.0, "cost_efficiency": 8.0, "credits_used": 2}}
        ),
        budget_engine=BudgetEngine(),
        selector=VendorSelector(),
        repo=repo,
    )
    req = ProcurementRunRequest(
        objective="buy trend data",
        vendors=[
            VendorCandidate(vendor_id="v1", vendor_name="Vendor 1", endpoint="https://v1.test", plan_id="p1", agent_id="a1", query="q1", expected_credits=2),
            VendorCandidate(vendor_id="v2", vendor_name="Vendor 2", endpoint="https://v2.test", plan_id="p2", agent_id="a2", query="q2", expected_credits=2),
        ],
    )
    decisions, pending = director.run("trace-repeat", req, mindra_execution_id="exec-1")
    assert not pending
    assert decisions[0].action == "repeat"
    assert decisions[0].selected_vendor_id == "v1"

    repo_low = _repo(tmp_path / "switch")
    repo_low.upsert_vendor_profile("v1", "Vendor 1", "https://v1.test", 3.5, 3.5, 3.5, 3.5, 3.5)
    repo_low.upsert_vendor_profile("v2", "Vendor 2", "https://v2.test", 6.0, 6.0, 6.0, 6.0, 6.0)
    repo_low.record_purchase("s1", "v1", "https://v1.test", 2, 3, 3, 4, 4, 3.5, {}, idempotency_key="sp1")
    repo_low.record_purchase("s2", "v1", "https://v1.test", 2, 3, 3, 4, 4, 3.6, {}, idempotency_key="sp2")
    repo_low.record_purchase("s3", "v1", "https://v1.test", 2, 3, 3, 4, 4, 3.4, {}, idempotency_key="sp3")
    director_low = ProcurementDirector(
        market_scout=FakeMarketScout(
            {"v2": {"quality": 8.0, "compliance": 8.0, "latency_score": 8.0, "cost_efficiency": 8.0, "credits_used": 2}}
        ),
        budget_engine=BudgetEngine(),
        selector=VendorSelector(),
        repo=repo_low,
    )
    req_low = ProcurementRunRequest(
        objective="buy compliance data",
        vendors=[
            VendorCandidate(vendor_id="v1", vendor_name="Vendor 1", endpoint="https://v1.test", plan_id="p1", agent_id="a1", query="q1", expected_credits=2),
            VendorCandidate(vendor_id="v2", vendor_name="Vendor 2", endpoint="https://v2.test", plan_id="p2", agent_id="a2", query="q2", expected_credits=2),
        ],
    )
    decisions_low, pending_low = director_low.run("trace-switch", req_low, mindra_execution_id="exec-2")
    assert not pending_low
    assert decisions_low[0].action == "switch"
    assert decisions_low[0].selected_vendor_id == "v2"


def test_procurement_pending_approval(tmp_path):
    repo = _repo(tmp_path)
    director = ProcurementDirector(
        market_scout=FakeMarketScout({}),
        budget_engine=BudgetEngine(),
        selector=VendorSelector(),
        repo=repo,
    )
    req = ProcurementRunRequest(
        objective="buy expensive route",
        vendors=[
            VendorCandidate(
                vendor_id="v1",
                vendor_name="Vendor 1",
                endpoint="https://v1.test",
                plan_id="p1",
                agent_id="a1",
                query="q1",
                expected_credits=11,
            )
        ],
    )
    decisions, pending = director.run(
        "trace-approval",
        req,
        mindra_execution_id="exec-approval",
        mindra_approval_id="apr-1",
    )
    assert pending
    assert decisions[0].action == "pending_approval"
    assert decisions[0].mindra_execution_id == "exec-approval"
    assert decisions[0].mindra_approval_id == "apr-1"


def test_current_vendor_uses_latest_purchase_not_largest_history(tmp_path):
    repo = _repo(tmp_path)
    repo.upsert_vendor_profile("v1", "Vendor 1", "https://v1.test", 8.0, 8.0, 8.0, 8.0, 8.0)
    repo.upsert_vendor_profile("v2", "Vendor 2", "https://v2.test", 8.0, 8.0, 8.0, 8.0, 8.0)
    repo.record_purchase("t1", "v1", "https://v1.test", 2, 8, 8, 8, 8, 8.0, {}, idempotency_key="lp1")
    repo.record_purchase("t2", "v1", "https://v1.test", 2, 8, 8, 8, 8, 8.0, {}, idempotency_key="lp2")
    repo.record_purchase("t3", "v1", "https://v1.test", 2, 8, 8, 8, 8, 8.0, {}, idempotency_key="lp3")
    repo.record_purchase("t4", "v2", "https://v2.test", 2, 8, 8, 8, 8, 8.0, {}, idempotency_key="lp4")

    director = ProcurementDirector(
        market_scout=FakeMarketScout(
            {"v2": {"quality": 8.0, "compliance": 8.0, "latency_score": 8.0, "cost_efficiency": 8.0, "credits_used": 2}}
        ),
        budget_engine=BudgetEngine(),
        selector=VendorSelector(),
        repo=repo,
    )
    req = ProcurementRunRequest(
        objective="buy more trend data",
        vendors=[
            VendorCandidate(vendor_id="v1", vendor_name="Vendor 1", endpoint="https://v1.test", plan_id="p1", agent_id="a1", query="q1", expected_credits=2),
            VendorCandidate(vendor_id="v2", vendor_name="Vendor 2", endpoint="https://v2.test", plan_id="p2", agent_id="a2", query="q2", expected_credits=2),
        ],
    )

    decisions, pending = director.run("trace-latest", req, mindra_execution_id="exec-latest")
    assert not pending
    assert decisions[0].action == "repeat"
    assert decisions[0].selected_vendor_id == "v2"


pytestmark = pytest.mark.live


def _missing_env() -> list[str]:
    required = [
        "CREATORFORGE_LIVE_TEST",
        "OPENAI_API_KEY",
        "NVM_API_KEY",
        "NVM_PLAN_ID",
        "NVM_AGENT_ID",
        "MINDRA_BASE_URL",
        "MINDRA_API_KEY",
        "MINDRA_WORKFLOW_SLUG_CREATIVE",
        "MINDRA_WORKFLOW_SLUG_PROCUREMENT",
        "ZEROCLICK_API_URL",
        "ZEROCLICK_API_KEY",
        "LIVE_VENDOR_ENDPOINT",
        "LIVE_VENDOR_PLAN_ID",
        "LIVE_VENDOR_AGENT_ID",
    ]
    return [name for name in required if not os.getenv(name)]


def test_live_procurement_flow():
    missing = _missing_env()
    if missing:
        pytest.skip(f"missing live env vars: {', '.join(missing)}")

    if os.getenv("CREATORFORGE_LIVE_TEST") != "1":
        pytest.skip("set CREATORFORGE_LIVE_TEST=1 to enable live procurement test")

    app = create_app()
    client = TestClient(app)

    payload = {
        "objective": "buy compliance + trend data for creative optimization",
        "auto_approve": True,
        "vendors": [
            {
                "vendor_id": "live-vendor-1",
                "vendor_name": "Live Vendor",
                "endpoint": os.environ["LIVE_VENDOR_ENDPOINT"],
                "plan_id": os.environ["LIVE_VENDOR_PLAN_ID"],
                "agent_id": os.environ["LIVE_VENDOR_AGENT_ID"],
                "expected_credits": 2,
                "query": "Provide latest audience sentiment summary for fitness apps",
            }
        ],
    }

    resp = client.post("/v1/procurement/run", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["decisions"]
