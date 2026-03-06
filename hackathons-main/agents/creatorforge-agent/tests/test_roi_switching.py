from src.procurement.roi_engine import compute_roi, rolling_roi, should_repeat, should_switch
from src.procurement.vendor_selector import VendorSelector, VendorState


def test_compute_roi_matches_locked_formula():
    score = compute_roi(quality=8.0, compliance=6.0, latency_score=7.0, cost_efficiency=5.0)
    assert score == 6.9


def test_switch_rule():
    assert should_switch(rolling=3.5, alternate_forecast=5.5, min_samples=3)
    assert not should_switch(rolling=4.2, alternate_forecast=6.0, min_samples=3)


def test_repeat_rule():
    assert should_repeat(rolling=7.0, last_success=True, cap_ok=True)
    assert not should_repeat(rolling=6.9, last_success=True, cap_ok=True)


def test_vendor_selector_repeat_precedence():
    selector = VendorSelector()
    current = VendorState("v1", rolling_roi=8.0, forecast_roi=8.0, recent_samples=4, last_success=True)
    candidates = [current, VendorState("v2", rolling_roi=7.0, forecast_roi=7.0, recent_samples=4, last_success=True)]
    action, reason = selector.select(current=current, candidates=candidates, cap_ok=True)
    assert action == "repeat"
    assert "repeat vendor" in reason


def test_vendor_selector_switch():
    selector = VendorSelector()
    current = VendorState("v1", rolling_roi=3.2, forecast_roi=3.2, recent_samples=3, last_success=True)
    candidates = [current, VendorState("v2", rolling_roi=6.0, forecast_roi=6.0, recent_samples=1, last_success=True)]
    action, reason = selector.select(current=current, candidates=candidates, cap_ok=True)
    assert action == "switch"
    assert "switch from v1" in reason


def test_vendor_selector_does_not_switch_to_self():
    selector = VendorSelector()
    current = VendorState("v1", rolling_roi=3.2, forecast_roi=7.5, recent_samples=3, last_success=True)
    action, reason = selector.select(current=current, candidates=[current], cap_ok=True)
    assert action == "hold"
    assert "hold current vendor" in reason
