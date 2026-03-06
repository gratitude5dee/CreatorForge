from src.pricing.policy import PricingPolicy


def test_base_quote_no_modifiers():
    policy = PricingPolicy()
    quote = policy.quote("visual", buyer_id="new-buyer", repeat_buyer=False, peak_demand=False)
    assert quote.base_credits == 3
    assert quote.effective_credits == 3.0
    assert quote.settlement_credits == 3
    assert quote.modifiers == []


def test_repeat_buyer_discount_applies():
    policy = PricingPolicy()
    quote = policy.quote("campaign", buyer_id="repeat-buyer", repeat_buyer=True, peak_demand=False)
    assert quote.base_credits == 10
    assert quote.effective_credits == 9.0
    assert quote.settlement_credits == 9
    assert any(m.name == "repeat-buyer-discount" for m in quote.modifiers)


def test_peak_demand_surcharge_campaign_only():
    policy = PricingPolicy()
    campaign_quote = policy.quote("campaign", buyer_id="b", repeat_buyer=False, peak_demand=True)
    ad_copy_quote = policy.quote("ad-copy", buyer_id="b", repeat_buyer=False, peak_demand=True)

    assert campaign_quote.settlement_credits == 12
    assert any(m.name == "peak-demand-surcharge" for m in campaign_quote.modifiers)
    assert ad_copy_quote.settlement_credits == 1
