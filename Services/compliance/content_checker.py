"""Platform compliance checker for affiliate content."""

from __future__ import annotations

from pydantic import BaseModel


class ComplianceRule(BaseModel):
    rule_id: str
    name: str
    platform: str
    category: str  # disclosure | char_limit | banned_words | hashtag
    description: str
    max_value: int = 0


class ComplianceResult(BaseModel):
    passed: bool
    issues: list[dict]
    score: int  # 0-100
    platform: str


# ---------------------------------------------------------------------------
# Platform-specific compliance rules
# ---------------------------------------------------------------------------

PLATFORM_RULES: dict[str, list[ComplianceRule]] = {
    "tiktok": [
        ComplianceRule(
            rule_id="TK-001",
            name="Character Limit",
            platform="tiktok",
            category="char_limit",
            description="Caption max 300 chars",
            max_value=300,
        ),
        ComplianceRule(
            rule_id="TK-002",
            name="Affiliate Disclosure",
            platform="tiktok",
            category="disclosure",
            description="Must include #affiliate or #ad for sponsored content",
        ),
        ComplianceRule(
            rule_id="TK-003",
            name="No Spam Hashtags",
            platform="tiktok",
            category="hashtag",
            description="Max 5 hashtags recommended",
        ),
    ],
    "instagram": [
        ComplianceRule(
            rule_id="IG-001",
            name="Character Limit",
            platform="instagram",
            category="char_limit",
            description="Caption max 2200 chars",
            max_value=2200,
        ),
        ComplianceRule(
            rule_id="IG-002",
            name="Affiliate Disclosure",
            platform="instagram",
            category="disclosure",
            description="Must include #ad or #sponsored",
        ),
        ComplianceRule(
            rule_id="IG-003",
            name="Hashtag Limit",
            platform="instagram",
            category="hashtag",
            description="Max 30 hashtags, 5-10 recommended",
        ),
    ],
    "facebook": [
        ComplianceRule(
            rule_id="FB-001",
            name="Character Limit",
            platform="facebook",
            category="char_limit",
            description="Post max 63206 chars",
            max_value=63206,
        ),
        ComplianceRule(
            rule_id="FB-002",
            name="Affiliate Disclosure",
            platform="facebook",
            category="disclosure",
            description="Must disclose affiliate relationships",
        ),
    ],
    "twitter": [
        ComplianceRule(
            rule_id="TW-001",
            name="Character Limit",
            platform="twitter",
            category="char_limit",
            description="Tweet max 280 chars",
            max_value=280,
        ),
        ComplianceRule(
            rule_id="TW-002",
            name="Affiliate Disclosure",
            platform="twitter",
            category="disclosure",
            description="Include #ad for sponsored",
        ),
    ],
    "youtube": [
        ComplianceRule(
            rule_id="YT-001",
            name="Title Length",
            platform="youtube",
            category="char_limit",
            description="Title max 100 chars",
            max_value=100,
        ),
        ComplianceRule(
            rule_id="YT-002",
            name="Description Length",
            platform="youtube",
            category="char_limit",
            description="Description max 5000 chars",
            max_value=5000,
        ),
        ComplianceRule(
            rule_id="YT-003",
            name="Affiliate Disclosure",
            platform="youtube",
            category="disclosure",
            description="Must include disclosure in description",
        ),
    ],
}

BANNED_WORDS: list[str] = [
    "guarantee",
    "guaranteed",
    "miracle",
    "cure",
    "heal",
    "100%",
    "free money",
    "no risk",
    "double your money",
]

DISCLOSURE_KEYWORDS: list[str] = [
    "#ad",
    "#affiliate",
    "#sponsored",
    "*affiliate",
    "#paid",
]


class ContentComplianceChecker:
    """Checks content against platform-specific compliance rules."""

    def check_content(
        self,
        content: str,
        platform: str,
        has_affiliate: bool = True,
    ) -> ComplianceResult:
        rules = PLATFORM_RULES.get(platform, [])
        issues: list[dict] = []
        score = 100

        for rule in rules:
            if rule.category == "char_limit" and rule.max_value and len(content) > rule.max_value:
                issues.append(
                    {
                        "rule": rule.rule_id,
                        "severity": "error",
                        "message": (
                            f"Content exceeds {rule.max_value} char limit "
                            f"({len(content)} chars)"
                        ),
                    },
                )
                score -= 20

            elif rule.category == "hashtag":
                hashtag_count = content.count("#")
                if hashtag_count > 10:
                    issues.append(
                        {
                            "rule": rule.rule_id,
                            "severity": "warning",
                            "message": (
                                f"Too many hashtags ({hashtag_count}). "
                                "Recommended: 5-10"
                            ),
                        },
                    )
                    score -= 10

            elif rule.category == "disclosure" and has_affiliate:
                content_lower = content.lower()
                if not any(kw.lower() in content_lower for kw in DISCLOSURE_KEYWORDS):
                    issues.append(
                        {
                            "rule": rule.rule_id,
                            "severity": "warning",
                            "message": (
                                "Missing affiliate disclosure. "
                                "Add #ad or #affiliate"
                            ),
                        },
                    )
                    score -= 15

        # Banned words check (cross-platform)
        lower = content.lower()
        for word in BANNED_WORDS:
            if word in lower:
                issues.append(
                    {
                        "rule": "BANNED",
                        "severity": "error",
                        "message": f"Banned word detected: '{word}'",
                    },
                )
                score -= 25

        return ComplianceResult(
            passed=score >= 70,
            issues=issues,
            score=max(0, score),
            platform=platform,
        )
