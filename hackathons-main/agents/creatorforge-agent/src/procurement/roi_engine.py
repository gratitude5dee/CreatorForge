"""ROI scoring and repeat/switch policy engine."""

from __future__ import annotations


def compute_roi(
    quality: float,
    compliance: float,
    latency_score: float,
    cost_efficiency: float,
) -> float:
    """Compute normalized ROI (0..10) from policy weights."""
    score = (
        0.40 * quality
        + 0.25 * compliance
        + 0.20 * latency_score
        + 0.15 * cost_efficiency
    )
    return max(0.0, min(10.0, round(score, 2)))


def rolling_roi(values: list[float], window: int = 3) -> float:
    """Return rolling ROI average for the trailing window."""
    if not values:
        return 0.0
    recent = values[-window:]
    return round(sum(recent) / len(recent), 2)


def should_switch(rolling: float, alternate_forecast: float, min_samples: int) -> bool:
    """Switch provider policy: ROI < 4.0 and alternative forecast >= 5.5."""
    return min_samples >= 3 and rolling < 4.0 and alternate_forecast >= 5.5


def should_repeat(rolling: float, last_success: bool, cap_ok: bool) -> bool:
    """Repeat policy: rolling ROI >= 7.0, last success, and cap is OK."""
    return rolling >= 7.0 and last_success and cap_ok
