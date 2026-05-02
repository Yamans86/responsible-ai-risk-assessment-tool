"""Risk scoring logic for Responsible AI assessments."""

from __future__ import annotations

from src.regulations import evaluate_regulatory_exposure
from src.risk_rules import get_provider_profile


DATA_WEIGHTS = {
    "personal_data": 5,
    "sensitive_data": 8,
    "vulnerable_groups": 5,
    "external_data": 4,
    "data_quality_uncertain": 5,
    "cross_border_transfer": 3,
}

MODEL_WEIGHTS = {
    "generative_ai": 4,
    "autonomous_decisions": 6,
    "opaque_model": 4,
    "custom_training": 4,
    "continuous_learning": 3,
    "performance_untested": 4,
}

IMPACT_WEIGHTS = {
    "high_stakes_domain": 8,
    "large_scale": 4,
    "user_harm_possible": 6,
    "vulnerable_impact": 5,
    "public_facing": 3,
    "limited_human_review": 4,
}

GOVERNANCE_WEIGHTS = {
    "no_owner": 3,
    "no_documentation": 3,
    "no_monitoring": 3,
    "no_incident_process": 2,
    "no_human_oversight": 2,
    "supplier_controls_missing": 2,
}

SUPPLIER_GOVERNANCE_WEIGHTS = {
    "third_party_involved": 2,
    "missing_supplier_names": 2,
    "missing_supplier_model_usage": 2,
}

CPMAI_DATA_WEIGHTS = {
    "data_requirements_unclear": 4,
    "data_quantity_insufficient": 3,
    "ground_truth_missing": 4,
    "data_access_unresolved": 3,
    "pipeline_or_labeling_controls_missing": 4,
}

CPMAI_MODEL_WEIGHTS = {
    "ai_fit_unvalidated": 4,
    "model_validation_plan_missing": 4,
    "train_validation_test_split_missing": 3,
    "drift_retraining_plan_missing": 4,
    "genai_production_controls_missing": 3,
}

CPMAI_IMPACT_WEIGHTS = {
    "business_problem_unclear": 4,
    "success_metrics_missing": 4,
    "roi_not_estimated": 3,
    "user_acceptance_change_risk": 3,
    "limits_not_defined": 4,
}

CPMAI_GOVERNANCE_WEIGHTS = {
    "go_no_go_criteria_missing": 3,
    "project_team_roles_missing": 2,
    "audit_traceability_missing": 3,
    "operational_readiness_missing": 3,
    "security_review_missing": 2,
}

CATEGORY_MAXIMUMS = {
    "data": 30,
    "model": 25,
    "impact": 30,
    "governance": 15,
}


def calculate_category_score(inputs: dict, weights: dict, maximum: int) -> int:
    """Return a capped score for a risk category."""

    score = sum(weight for key, weight in weights.items() if inputs.get(key))
    return min(score, maximum)


def calculate_supplier_governance_score(assessment: dict) -> int:
    """Return governance risk points from supplier involvement and documentation gaps."""

    if not assessment.get("third_party_involved"):
        return 0

    score = SUPPLIER_GOVERNANCE_WEIGHTS["third_party_involved"]

    if not assessment.get("suppliers"):
        score += SUPPLIER_GOVERNANCE_WEIGHTS["missing_supplier_names"]
    if not assessment.get("model_usage_supplier"):
        score += SUPPLIER_GOVERNANCE_WEIGHTS["missing_supplier_model_usage"]

    return score


def calculate_cpmai_scores(assessment: dict) -> dict:
    """Return risk points derived from CPMAI project-readiness controls."""

    cpmai = assessment.get("cpmai", {})
    return {
        "data": calculate_category_score(cpmai, CPMAI_DATA_WEIGHTS, CATEGORY_MAXIMUMS["data"]),
        "model": calculate_category_score(cpmai, CPMAI_MODEL_WEIGHTS, CATEGORY_MAXIMUMS["model"]),
        "impact": calculate_category_score(cpmai, CPMAI_IMPACT_WEIGHTS, CATEGORY_MAXIMUMS["impact"]),
        "governance": calculate_category_score(
            cpmai,
            CPMAI_GOVERNANCE_WEIGHTS,
            CATEGORY_MAXIMUMS["governance"],
        ),
    }


def calculate_provider_risk_scores(assessment: dict) -> dict:
    """Return category risk points from the selected provider trust profile."""

    profile = get_provider_profile(
        assessment.get("model_provider", "Internal / no external foundation model")
    )
    return {
        "data": profile["data_risk"],
        "model": profile["model_risk"],
        "governance": profile["governance_risk"],
    }


def score_assessment(assessment: dict) -> dict:
    """Calculate category scores and total risk score for an assessment."""

    provider_scores = calculate_provider_risk_scores(assessment)
    cpmai_scores = calculate_cpmai_scores(assessment)
    regulatory_scores = evaluate_regulatory_exposure(assessment)["scores"]
    data_score = min(
        calculate_category_score(
            assessment.get("data", {}),
            DATA_WEIGHTS,
            CATEGORY_MAXIMUMS["data"],
        )
        + provider_scores["data"]
        + cpmai_scores["data"]
        + regulatory_scores["data"],
        CATEGORY_MAXIMUMS["data"],
    )
    model_score = min(
        calculate_category_score(
            assessment.get("model", {}),
            MODEL_WEIGHTS,
            CATEGORY_MAXIMUMS["model"],
        )
        + provider_scores["model"]
        + cpmai_scores["model"]
        + regulatory_scores["model"],
        CATEGORY_MAXIMUMS["model"],
    )
    impact_score = min(
        calculate_category_score(
            assessment.get("impact", {}),
            IMPACT_WEIGHTS,
            CATEGORY_MAXIMUMS["impact"],
        )
        + cpmai_scores["impact"]
        + regulatory_scores["impact"],
        CATEGORY_MAXIMUMS["impact"],
    )
    governance_base_score = calculate_category_score(
        assessment.get("governance", {}),
        GOVERNANCE_WEIGHTS,
        CATEGORY_MAXIMUMS["governance"],
    )
    governance_score = min(
        governance_base_score
        + calculate_supplier_governance_score(assessment)
        + provider_scores["governance"]
        + cpmai_scores["governance"]
        + regulatory_scores["governance"],
        CATEGORY_MAXIMUMS["governance"],
    )

    total = data_score + model_score + impact_score + governance_score

    return {
        "data": data_score,
        "model": model_score,
        "impact": impact_score,
        "governance": governance_score,
        "total": min(total, 100),
    }
