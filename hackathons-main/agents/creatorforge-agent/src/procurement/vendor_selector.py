"""Vendor decision logic for buy/repeat/switch behavior."""

from __future__ import annotations

from dataclasses import dataclass

from .roi_engine import should_repeat, should_switch


@dataclass(frozen=True)
class VendorState:
    vendor_id: str
    rolling_roi: float
    forecast_roi: float
    recent_samples: int
    last_success: bool


class VendorSelector:
    """Decides procurement action from vendor state."""

    def select(self, current: VendorState | None, candidates: list[VendorState], cap_ok: bool) -> tuple[str, str]:
        if not candidates:
            return "blocked", "no candidate vendors provided"

        best = max(candidates, key=lambda c: c.forecast_roi)
        if current is None:
            return "buy_new", f"selected best forecast vendor {best.vendor_id}"

        alternates = [candidate for candidate in candidates if candidate.vendor_id != current.vendor_id]
        best_alternate = max(alternates, key=lambda c: c.forecast_roi) if alternates else None

        if should_repeat(current.rolling_roi, current.last_success, cap_ok):
            return "repeat", f"repeat vendor {current.vendor_id} due to rolling ROI {current.rolling_roi}"

        if best_alternate and should_switch(current.rolling_roi, best_alternate.forecast_roi, current.recent_samples):
            return "switch", (
                f"switch from {current.vendor_id} (rolling ROI {current.rolling_roi}) "
                f"to {best_alternate.vendor_id} (forecast {best_alternate.forecast_roi})"
            )

        return "hold", f"hold current vendor {current.vendor_id}; no switch/repeat condition met"
