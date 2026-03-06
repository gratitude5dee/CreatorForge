"""Repository for CreatorForge persistent entities."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from .db import Database


class Repository:
    def __init__(self, db: Database):
        self.db = db

    def create_campaign(self, trace_id: str, service: str, buyer_id: str, brief: str, status: str = "received") -> int:
        return self.db.execute(
            "INSERT INTO campaigns (trace_id, service, buyer_id, brief, status) VALUES (?, ?, ?, ?, ?)",
            (trace_id, service, buyer_id, brief, status),
        )

    def create_creative_asset(
        self,
        campaign_id: int,
        trace_id: str,
        service: str,
        content: dict,
        quality: dict,
        ad_context: dict | None,
    ) -> int:
        return self.db.execute(
            """
            INSERT INTO creative_assets (campaign_id, trace_id, service, content_json, quality_json, ad_context_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                campaign_id,
                trace_id,
                service,
                json.dumps(content),
                json.dumps(quality),
                json.dumps(ad_context) if ad_context else None,
            ),
        )

    def record_sale(self, trace_id: str, buyer_id: str, service: str, credits: int, settlement: dict) -> int:
        return self.db.execute(
            "INSERT INTO sales (trace_id, buyer_id, service, credits, settlement_json) VALUES (?, ?, ?, ?, ?)",
            (trace_id, buyer_id, service, credits, json.dumps(settlement)),
        )

    def record_purchase(
        self,
        trace_id: str,
        vendor_id: str,
        endpoint: str,
        credits: int,
        quality: float,
        compliance: float,
        latency_score: float,
        cost_efficiency: float,
        roi_score: float,
        settlement: dict,
    ) -> int:
        return self.db.execute(
            """
            INSERT INTO purchases (
              trace_id, vendor_id, endpoint, credits,
              quality, compliance, latency_score, cost_efficiency, roi_score, settlement_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                vendor_id,
                endpoint,
                credits,
                quality,
                compliance,
                latency_score,
                cost_efficiency,
                roi_score,
                json.dumps(settlement),
            ),
        )

    def record_budget_entry(self, trace_id: str, vendor_id: str, credits: int, direction: str, note: str = "") -> int:
        return self.db.execute(
            "INSERT INTO budget_ledger (trace_id, vendor_id, credits, direction, note) VALUES (?, ?, ?, ?, ?)",
            (trace_id, vendor_id, credits, direction, note),
        )

    def upsert_vendor_profile(
        self,
        vendor_id: str,
        vendor_name: str,
        endpoint: str,
        rolling_roi: float,
        quality: float,
        compliance: float,
        latency: float,
        cost_efficiency: float,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO vendor_profiles (
              vendor_id, vendor_name, endpoint, rolling_roi,
              last_quality, last_compliance, last_latency, last_cost_efficiency, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vendor_id)
            DO UPDATE SET
              vendor_name=excluded.vendor_name,
              endpoint=excluded.endpoint,
              rolling_roi=excluded.rolling_roi,
              last_quality=excluded.last_quality,
              last_compliance=excluded.last_compliance,
              last_latency=excluded.last_latency,
              last_cost_efficiency=excluded.last_cost_efficiency,
              updated_at=excluded.updated_at
            """,
            (
                vendor_id,
                vendor_name,
                endpoint,
                rolling_roi,
                quality,
                compliance,
                latency,
                cost_efficiency,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

    def list_vendor_profiles(self) -> list[dict]:
        return self.db.fetchall(
            "SELECT vendor_id, vendor_name, endpoint, rolling_roi, updated_at FROM vendor_profiles ORDER BY rolling_roi DESC"
        )

    def create_procurement_decision(
        self,
        trace_id: str,
        selected_vendor_id: str,
        action: str,
        reason: str,
        roi_score: float | None,
        alternate_forecast: float | None,
        approval_request_id: int | None,
    ) -> int:
        return self.db.execute(
            """
            INSERT INTO procurement_decisions (
              trace_id, selected_vendor_id, action, reason, roi_score, alternate_forecast, approval_request_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (trace_id, selected_vendor_id, action, reason, roi_score, alternate_forecast, approval_request_id),
        )

    def get_procurement_decision(self, decision_id: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM procurement_decisions WHERE id = ?", (decision_id,))

    def create_approval_request(self, trace_id: str, vendor_id: str, credits: int, reason: str) -> int:
        return self.db.execute(
            "INSERT INTO approval_requests (trace_id, vendor_id, credits, reason) VALUES (?, ?, ?, ?)",
            (trace_id, vendor_id, credits, reason),
        )

    def list_pending_approvals(self) -> list[dict]:
        return self.db.fetchall(
            "SELECT id, trace_id, vendor_id, credits, status, reason, created_at FROM approval_requests WHERE status = 'pending' ORDER BY id ASC"
        )

    def resolve_approval(self, approval_id: int, approved: bool, reviewer: str, note: str | None) -> None:
        status = "approved" if approved else "rejected"
        self.db.execute(
            """
            UPDATE approval_requests
            SET status = ?, reviewer = ?, note = ?, decided_at = ?
            WHERE id = ?
            """,
            (status, reviewer, note, datetime.now(timezone.utc).isoformat(), approval_id),
        )

    def get_approval(self, approval_id: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM approval_requests WHERE id = ?", (approval_id,))

    def record_ad_event(self, trace_id: str, event: str, provider: str, payload: dict) -> int:
        return self.db.execute(
            "INSERT INTO ad_events (trace_id, event, provider, payload_json) VALUES (?, ?, ?, ?)",
            (trace_id, event, provider, json.dumps(payload)),
        )

    def record_audit_event(self, trace_id: str, agent_name: str, action: str, payload: dict) -> int:
        return self.db.execute(
            "INSERT INTO audit_events (trace_id, agent_name, action, payload_json) VALUES (?, ?, ?, ?)",
            (trace_id, agent_name, action, json.dumps(payload)),
        )

    def buyer_sale_count(self, buyer_id: str) -> int:
        row = self.db.fetchone("SELECT COUNT(*) AS c FROM sales WHERE buyer_id = ?", (buyer_id,))
        return int(row["c"]) if row else 0

    def daily_spend(self) -> int:
        row = self.db.fetchone(
            "SELECT COALESCE(SUM(credits), 0) AS c FROM budget_ledger WHERE direction = 'buy' AND date(created_at) = date('now')"
        )
        return int(row["c"]) if row else 0

    def vendor_daily_spend(self, vendor_id: str) -> int:
        row = self.db.fetchone(
            """
            SELECT COALESCE(SUM(credits), 0) AS c
            FROM budget_ledger
            WHERE direction = 'buy' AND vendor_id = ? AND date(created_at) = date('now')
            """,
            (vendor_id,),
        )
        return int(row["c"]) if row else 0

    def vendor_recent_rois(self, vendor_id: str, limit: int = 3) -> list[float]:
        rows = self.db.fetchall(
            "SELECT roi_score FROM purchases WHERE vendor_id = ? ORDER BY id DESC LIMIT ?",
            (vendor_id, limit),
        )
        return [float(r["roi_score"]) for r in rows][::-1]

    def get_stats(self) -> dict:
        sale_row = self.db.fetchone("SELECT COUNT(*) AS c, COALESCE(SUM(credits), 0) AS credits FROM sales") or {"c": 0, "credits": 0}
        buy_row = self.db.fetchone("SELECT COUNT(*) AS c, COALESCE(SUM(credits), 0) AS credits FROM purchases") or {"c": 0, "credits": 0}
        ad_row = self.db.fetchone("SELECT COUNT(*) AS c FROM ad_events") or {"c": 0}
        return {
            "sales_count": int(sale_row["c"]),
            "sales_credits": int(sale_row["credits"]),
            "purchases_count": int(buy_row["c"]),
            "purchases_credits": int(buy_row["credits"]),
            "ad_events": int(ad_row["c"]),
            "vendors": len(self.list_vendor_profiles()),
            "daily_spend": self.daily_spend(),
        }
