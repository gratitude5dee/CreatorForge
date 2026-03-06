import os

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


pytestmark = pytest.mark.live


def _missing_env() -> list[str]:
    required = [
        "CREATORFORGE_LIVE_TEST",
        "OPENAI_API_KEY",
        "NVM_API_KEY",
        "NVM_PLAN_ID",
        "NVM_AGENT_ID",
        "MINDRA_API_URL",
        "MINDRA_API_KEY",
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
