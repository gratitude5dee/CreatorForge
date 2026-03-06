"""Budget and approval gates for CreatorForge procurement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetCheck:
    allowed: bool
    reason: str
    approval_required: bool


class BudgetEngine:
    """Enforces daily and per-vendor spend constraints."""

    def __init__(self, daily_cap: int = 50, vendor_cap: int = 20, approval_threshold: int = 10):
        self.daily_cap = daily_cap
        self.vendor_cap = vendor_cap
        self.approval_threshold = approval_threshold

    def evaluate(self, credits: int, daily_spend: int, vendor_spend: int) -> BudgetCheck:
        if credits <= 0:
            return BudgetCheck(False, "credits must be positive", False)
        if daily_spend + credits > self.daily_cap:
            return BudgetCheck(False, "daily cap exceeded", False)
        if vendor_spend + credits > self.vendor_cap:
            return BudgetCheck(False, "per-vendor cap exceeded", False)
        approval_required = credits > self.approval_threshold
        if approval_required:
            return BudgetCheck(True, "requires human approval", True)
        return BudgetCheck(True, "approved by policy", False)
