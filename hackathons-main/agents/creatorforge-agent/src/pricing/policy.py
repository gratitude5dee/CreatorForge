"""Dynamic pricing policy for CreatorForge seller APIs."""

from __future__ import annotations

from datetime import datetime, timezone

from ..api.models import PricingModifier, PricingQuote, ServiceName

BASE_CREDITS: dict[ServiceName, int] = {
    "ad-copy": 1,
    "visual": 3,
    "brand-kit": 5,
    "campaign": 10,
    "ad-enriched": 2,
}


class PricingPolicy:
    """Compute buyer-facing and settlement pricing."""

    def get_base_credits(self, service: ServiceName) -> int:
        return BASE_CREDITS[service]

    def quote(
        self,
        service: ServiceName,
        buyer_id: str,
        repeat_buyer: bool,
        peak_demand: bool = False,
    ) -> PricingQuote:
        base = self.get_base_credits(service)
        effective = float(base)
        modifiers: list[PricingModifier] = []

        if repeat_buyer:
            effective *= 0.9
            modifiers.append(
                PricingModifier(
                    name="repeat-buyer-discount",
                    delta_percent=-10.0,
                    reason="10% retention discount for repeat buyers",
                )
            )

        if peak_demand and service == "campaign":
            effective *= 1.2
            modifiers.append(
                PricingModifier(
                    name="peak-demand-surcharge",
                    delta_percent=20.0,
                    reason="Campaign workload surge pricing",
                )
            )

        settlement = max(1, int(round(effective)))
        return PricingQuote(
            service=service,
            buyer_id=buyer_id,
            base_credits=base,
            effective_credits=round(effective, 2),
            settlement_credits=settlement,
            modifiers=modifiers,
            generated_at=datetime.now(timezone.utc),
        )
