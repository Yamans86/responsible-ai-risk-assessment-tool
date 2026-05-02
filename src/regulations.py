"""Regulatory exposure rules for AI and data risk screening."""

from __future__ import annotations


REGION_OPTIONS = [
    "United States",
    "California",
    "European Union / EEA",
    "United Kingdom",
    "Thailand",
    "Singapore",
    "Other / global",
]

HOST_REGION_OPTIONS = [
    "United States",
    "California",
    "European Union / EEA",
    "United Kingdom",
    "Thailand",
    "Singapore",
    "Multi-region / unknown",
    "Other",
]

CLOUD_PROVIDER_JURISDICTIONS = [
    "No cloud or external hosting",
    "US-controlled provider",
    "EU-controlled provider",
    "Local sovereign cloud",
    "Other non-US provider",
    "Unknown",
]

REGULATORY_REFERENCES = {
    "EU AI Act": "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
    "GDPR": "https://gdpr-info.eu/art-3-gdpr/",
    "UK GDPR": "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/",
    "HIPAA": "https://www.hhs.gov/hipaa/for-professionals/covered-entities/index.html",
    "CCPA / CPRA": "https://oag.ca.gov/privacy/ccpa",
    "Singapore PDPA": "https://www.pdpc.gov.sg/overview-of-pdpa/the-legislation/personal-data-protection-act/data-protection-obligations",
    "Thailand PDPA": "https://library.siam-legal.com/thai-law/personal-data-protection-act-general-provisions-sections-1-7/",
    "US CLOUD Act": "https://www.justice.gov/criminal/cloud-act-resources",
}


def _locations(assessment: dict) -> set[str]:
    """Return all selected organization, user, and hosting locations."""

    compliance = assessment.get("compliance", {})
    selected = set(compliance.get("target_regions", []))
    for key in ("organization_location", "data_host_region"):
        value = compliance.get(key)
        if value:
            selected.add(value)
    return selected


def _has_personal_data(assessment: dict) -> bool:
    """Return whether the project appears to process personal data."""

    data = assessment.get("data", {})
    compliance = assessment.get("compliance", {})
    return any(
        [
            data.get("personal_data"),
            data.get("sensitive_data"),
            data.get("vulnerable_groups"),
            compliance.get("handles_phi"),
            compliance.get("handles_california_personal_information"),
        ]
    )


def _has_sensitive_data(assessment: dict) -> bool:
    """Return whether sensitive or regulated data appears in scope."""

    data = assessment.get("data", {})
    compliance = assessment.get("compliance", {})
    return any(
        [
            data.get("sensitive_data"),
            data.get("vulnerable_groups"),
            compliance.get("handles_phi"),
            compliance.get("handles_california_sensitive_information"),
        ]
    )


def _is_eu_exposed(assessment: dict) -> bool:
    """Return whether EU or EEA exposure appears likely."""

    locations = _locations(assessment)
    return "European Union / EEA" in locations


def _is_uk_exposed(assessment: dict) -> bool:
    """Return whether UK exposure appears likely."""

    return "United Kingdom" in _locations(assessment)


def _is_us_exposed(assessment: dict) -> bool:
    """Return whether US exposure appears likely."""

    locations = _locations(assessment)
    return bool({"United States", "California"} & locations)


def _uses_us_controlled_cloud(assessment: dict) -> bool:
    """Return whether the cloud provider may be subject to US jurisdiction."""

    compliance = assessment.get("compliance", {})
    return compliance.get("cloud_provider_jurisdiction") == "US-controlled provider"


def _cloud_act_relevance(assessment: dict) -> bool:
    """Return whether Cloud Act review is relevant to the hosting pattern."""

    compliance = assessment.get("compliance", {})
    non_us_locations = _locations(assessment) - {"United States", "California"}
    hosted_outside_us = compliance.get("data_host_region") not in {
        "",
        None,
        "United States",
        "California",
    }
    return _uses_us_controlled_cloud(assessment) and bool(non_us_locations or hosted_outside_us)


def evaluate_regulatory_exposure(assessment: dict) -> dict:
    """Evaluate likely regulatory exposure and return scores, issues, and references."""

    data = assessment.get("data", {})
    model = assessment.get("model", {})
    impact = assessment.get("impact", {})
    compliance = assessment.get("compliance", {})
    organization_type = assessment.get("organization_type")
    use_case = assessment.get("use_case")

    scores = {"data": 0, "model": 0, "impact": 0, "governance": 0}
    exposures = []

    def add_exposure(
        name: str,
        reason: str,
        data_points: int = 0,
        model_points: int = 0,
        impact_points: int = 0,
        governance_points: int = 0,
    ) -> None:
        scores["data"] += data_points
        scores["model"] += model_points
        scores["impact"] += impact_points
        scores["governance"] += governance_points
        exposures.append(
            {
                "name": name,
                "reason": reason,
                "data_points": data_points,
                "model_points": model_points,
                "impact_points": impact_points,
                "governance_points": governance_points,
                "reference": REGULATORY_REFERENCES[name],
            }
        )

    if _has_personal_data(assessment) and _is_eu_exposed(assessment):
        add_exposure(
            "GDPR",
            "EU/EEA organization, users, data subjects, or hosting are in scope while personal data is processed.",
            data_points=3 + (2 if _has_sensitive_data(assessment) else 0),
            governance_points=2
            + (2 if compliance.get("no_lawful_basis_or_notice") else 0)
            + (2 if compliance.get("no_dpia_or_transfer_assessment") else 0),
        )

    if _has_personal_data(assessment) and _is_uk_exposed(assessment):
        add_exposure(
            "UK GDPR",
            "UK organization, users, data subjects, or hosting are in scope while personal data is processed.",
            data_points=2 + (1 if _has_sensitive_data(assessment) else 0),
            governance_points=1 + (2 if compliance.get("no_lawful_basis_or_notice") else 0),
        )

    eu_ai_trigger = _is_eu_exposed(assessment) and any(
        [
            impact.get("high_stakes_domain"),
            model.get("autonomous_decisions"),
            use_case
            in {
                "Hiring or workforce management",
                "Education or assessment",
                "Public services or benefits",
                "Safety, security, or law enforcement",
                "Financial eligibility or pricing",
                "Healthcare or wellbeing",
            },
        ]
    )
    if eu_ai_trigger:
        add_exposure(
            "EU AI Act",
            "EU/EEA exposure plus a potentially high-impact AI use case requires AI Act classification and high-risk controls review.",
            model_points=2,
            impact_points=4,
            governance_points=3 + (3 if compliance.get("no_ai_act_classification") else 0),
        )

    if _is_us_exposed(assessment) and (
        compliance.get("handles_phi")
        or (organization_type == "Healthcare" and (data.get("personal_data") or data.get("sensitive_data")))
    ):
        add_exposure(
            "HIPAA",
            "US healthcare context or protected health information may require HIPAA covered-entity, business-associate, and BAA review.",
            data_points=4,
            governance_points=3 + (3 if compliance.get("no_hipaa_baa") else 0),
        )

    if (
        "California" in _locations(assessment)
        and compliance.get("handles_california_personal_information")
        and organization_type == "Private sector"
    ):
        add_exposure(
            "CCPA / CPRA",
            "California residents' personal information is in scope for a private-sector project.",
            data_points=2 + (2 if compliance.get("handles_california_sensitive_information") else 0),
            governance_points=2 + (2 if compliance.get("no_consumer_rights_process") else 0),
        )

    if _has_personal_data(assessment) and "Singapore" in _locations(assessment):
        add_exposure(
            "Singapore PDPA",
            "Singapore organization, individuals, or hosting are in scope while personal data is processed.",
            data_points=2,
            governance_points=2 + (1 if compliance.get("no_lawful_basis_or_notice") else 0),
        )

    if _has_personal_data(assessment) and "Thailand" in _locations(assessment):
        add_exposure(
            "Thailand PDPA",
            "Thailand organization, individuals, or hosting are in scope while personal data is processed.",
            data_points=2,
            governance_points=2 + (1 if compliance.get("no_lawful_basis_or_notice") else 0),
        )

    if _cloud_act_relevance(assessment):
        add_exposure(
            "US CLOUD Act",
            "Data is hosted with a US-controlled provider or provider subject to US jurisdiction, while non-US data or non-US hosting may be involved.",
            data_points=2 + (1 if _has_sensitive_data(assessment) else 0),
            governance_points=2 + (3 if compliance.get("no_cloud_act_review") else 0),
        )

    return {"scores": scores, "exposures": exposures}
