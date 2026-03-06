"""Quality auditor specialist agent."""

from __future__ import annotations

from .tooling import strands_tool


class QualityAuditorAgent:
    """Deterministic validator for quality/compliance scoring."""

    def run(self, content: dict) -> dict:
        text_size = len(str(content))
        quality = min(10.0, max(1.0, round(text_size / 250, 2)))
        compliance = min(10.0, max(1.0, round((text_size % 900) / 90 + 1, 2)))
        status = "pass" if quality >= 4.0 and compliance >= 4.0 else "review"
        return {
            "quality_score": quality,
            "compliance_score": compliance,
            "status": status,
        }

    def gate(self, content: dict) -> tuple[bool, dict, str | None]:
        quality = self.run(content)
        if quality["status"] == "pass":
            return True, quality, None
        reason = (
            f"quality gate failed with quality={quality['quality_score']} "
            f"and compliance={quality['compliance_score']}"
        )
        return False, quality, reason

    def as_tool(self):
        @strands_tool
        def audit_creative_output(content: dict) -> dict:
            return self.run(content)

        return audit_creative_output
