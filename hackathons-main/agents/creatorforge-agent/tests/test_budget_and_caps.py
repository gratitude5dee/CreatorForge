from src.procurement.budget_engine import BudgetEngine


def test_budget_blocks_daily_cap():
    engine = BudgetEngine(daily_cap=50, vendor_cap=20, approval_threshold=10)
    result = engine.evaluate(credits=5, daily_spend=48, vendor_spend=0)
    assert not result.allowed
    assert result.reason == "daily cap exceeded"


def test_budget_blocks_vendor_cap():
    engine = BudgetEngine(daily_cap=50, vendor_cap=20, approval_threshold=10)
    result = engine.evaluate(credits=4, daily_spend=10, vendor_spend=18)
    assert not result.allowed
    assert result.reason == "per-vendor cap exceeded"


def test_budget_requires_approval_for_high_value_purchase():
    engine = BudgetEngine(daily_cap=50, vendor_cap=20, approval_threshold=10)
    result = engine.evaluate(credits=11, daily_spend=0, vendor_spend=0)
    assert result.allowed
    assert result.approval_required
