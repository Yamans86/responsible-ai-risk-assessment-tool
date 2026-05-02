"""Risk classification and explanation rules."""

from __future__ import annotations


PROVIDER_PROFILES = {
    "Internal / no external foundation model": {
        "provider": "Internal",
        "data_risk": 0,
        "model_risk": 0,
        "governance_risk": 0,
        "trust_label": "Internal baseline",
        "summary": "No external model provider is selected. Score depends on the project's own data, model, impact, and governance inputs.",
        "references": [],
    },
    "Azure OpenAI Service": {
        "provider": "Microsoft / OpenAI",
        "data_risk": 0,
        "model_risk": 1,
        "governance_risk": 0,
        "trust_label": "Lower provider data-sharing risk",
        "summary": "Microsoft states Azure OpenAI prompts, completions, embeddings, and training data are not available to OpenAI or other customers and are not used to train foundation models.",
        "references": [
            "https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy",
            "https://github.com/stanford-crfm/fmti",
        ],
    },
    "OpenAI API / ChatGPT Business or Enterprise": {
        "provider": "OpenAI",
        "data_risk": 1,
        "model_risk": 1,
        "governance_risk": 1,
        "trust_label": "Lower provider data-sharing risk",
        "summary": "OpenAI states API and business products are not used to train models by default, with separate retention and abuse-monitoring controls.",
        "references": [
            "https://platform.openai.com/docs/models/how-we-use-your-data",
            "https://openai.com/index/business-data",
            "https://github.com/stanford-crfm/fmti",
        ],
    },
    "Google Gemini API (paid or billing-enabled)": {
        "provider": "Google",
        "data_risk": 1,
        "model_risk": 1,
        "governance_risk": 1,
        "trust_label": "Lower provider data-sharing risk",
        "summary": "Google states paid Gemini API use does not use prompts or responses to improve products and is processed under its data processing terms.",
        "references": [
            "https://ai.google.dev/gemini-api/terms_preview",
            "https://ai.google.dev/gemini-api/docs/logs-policy",
            "https://github.com/stanford-crfm/fmti",
        ],
    },
    "Google Gemini API / AI Studio (unpaid)": {
        "provider": "Google",
        "data_risk": 6,
        "model_risk": 2,
        "governance_risk": 2,
        "trust_label": "Higher data-sharing risk",
        "summary": "Google states unpaid Gemini API or AI Studio content and generated responses may be used to provide, improve, and develop products and machine-learning technologies, and may be reviewed by humans.",
        "references": [
            "https://ai.google.dev/gemini-api/terms_preview",
        ],
    },
    "Anthropic Claude API / Claude for Work": {
        "provider": "Anthropic",
        "data_risk": 1,
        "model_risk": 1,
        "governance_risk": 1,
        "trust_label": "Lower provider data-sharing risk",
        "summary": "Anthropic states commercial customer data for Claude for Work and API services is processed on customer instructions and is not used to train generative models.",
        "references": [
            "https://support.anthropic.com/en/articles/9267385-does-anthropic-act-as-a-data-processor-or-controller",
            "https://github.com/stanford-crfm/fmti",
        ],
    },
    "Self-hosted open-source model": {
        "provider": "Self-hosted",
        "data_risk": 0,
        "model_risk": 4,
        "governance_risk": 3,
        "trust_label": "Contract risk lower, validation burden higher",
        "summary": "Self-hosting can reduce external data-sharing risk, but the organization must own safety evaluation, monitoring, security, patching, and model documentation.",
        "references": [
            "https://github.com/stanford-crfm/fmti",
        ],
    },
    "Other or unknown supplier model": {
        "provider": "Unknown",
        "data_risk": 4,
        "model_risk": 4,
        "governance_risk": 4,
        "trust_label": "Unknown provider risk",
        "summary": "Unknown providers add risk because data use, retention, safety controls, transparency, subprocessors, and audit rights have not been confirmed.",
        "references": [
            "https://github.com/stanford-crfm/fmti",
        ],
    },
}


def get_provider_profile(provider_name: str) -> dict:
    """Return the provider risk profile, falling back to unknown supplier risk."""

    return PROVIDER_PROFILES.get(provider_name, PROVIDER_PROFILES["Other or unknown supplier model"])


def classify_risk_level(total_score: int) -> str:
    """Classify total score into a qualitative risk level."""

    if total_score >= 75:
        return "Critical"
    if total_score >= 50:
        return "High"
    if total_score >= 25:
        return "Moderate"
    return "Low"


def explain_detected_risks(assessment: dict, scores: dict) -> list[str]:
    """Generate short explanations for major selected risk indicators."""

    explanations = []
    data = assessment.get("data", {})
    model = assessment.get("model", {})
    impact = assessment.get("impact", {})
    governance = assessment.get("governance", {})
    cpmai = assessment.get("cpmai", {})
    provider_profile = get_provider_profile(assessment.get("model_provider", "Internal / no external foundation model"))

    if scores.get("data", 0) >= 15:
        explanations.append(
            "Data risk is elevated because the project may involve sensitive, personal, external, "
            "or uncertain-provenance data."
        )
    if data.get("sensitive_data") or data.get("vulnerable_groups"):
        explanations.append(
            "Sensitive data or data about vulnerable groups requires stronger privacy, consent, "
            "access, retention, and minimization controls."
        )
    if scores.get("model", 0) >= 12:
        explanations.append(
            "Model risk is elevated because the system may be complex, difficult to explain, "
            "autonomous, changing over time, or insufficiently tested."
        )
    if model.get("autonomous_decisions") and impact.get("high_stakes_domain"):
        explanations.append(
            "Automated decisions in a high-stakes domain can create fairness, accountability, "
            "and contestability risks."
        )
    if scores.get("impact", 0) >= 15:
        explanations.append(
            "Impact risk is elevated because errors or misuse could affect people at scale, "
            "cause harm, or influence important outcomes."
        )
    if impact.get("limited_human_review"):
        explanations.append(
            "Limited human review increases reliance on model output and raises the need for "
            "clear escalation and override procedures."
        )
    if scores.get("governance", 0) >= 8:
        explanations.append(
            "Governance risk is elevated because key accountability, documentation, monitoring, "
            "oversight, or incident response controls may be missing."
        )
    if assessment.get("third_party_involved"):
        explanations.append(
            "Third-party model or supplier involvement adds governance risk because the project depends "
            "on external controls, contracts, service reliability, and audit access."
        )
    if assessment.get("third_party_involved") and not assessment.get("suppliers"):
        explanations.append(
            "Supplier names are missing, which makes ownership, due diligence, and contractual follow-up harder."
        )
    if assessment.get("third_party_involved") and not assessment.get("model_usage_supplier"):
        explanations.append(
            "Model usage by supplier is not documented, which makes it harder to assess dependency, data flow, "
            "and accountability risks."
        )
    if assessment.get("third_party_involved") and governance.get("supplier_controls_missing"):
        explanations.append(
            "Third-party involvement without supplier controls creates dependency, auditability, "
            "data protection, and contractual risk."
        )
    if provider_profile["data_risk"] or provider_profile["model_risk"] or provider_profile["governance_risk"]:
        explanations.append(
            f"Selected provider profile: {provider_profile['trust_label']}. {provider_profile['summary']}"
        )
    if cpmai.get("business_problem_unclear") or cpmai.get("ai_fit_unvalidated"):
        explanations.append(
            "CPMAI business-understanding risk is present because the problem, AI fit, or alternative approach has not been fully validated."
        )
    if cpmai.get("success_metrics_missing") or cpmai.get("roi_not_estimated"):
        explanations.append(
            "CPMAI value-realization risk is present because success metrics, expected benefits, or cost assumptions are incomplete."
        )
    if (
        cpmai.get("data_requirements_unclear")
        or cpmai.get("data_quantity_insufficient")
        or cpmai.get("ground_truth_missing")
        or cpmai.get("data_access_unresolved")
    ):
        explanations.append(
            "CPMAI data-understanding risk is present because data requirements, access, quantity, or ground-truth evidence may not support reliable AI delivery."
        )
    if cpmai.get("pipeline_or_labeling_controls_missing"):
        explanations.append(
            "CPMAI data-preparation risk is present because pipeline, labeling, or data quality controls are not yet defined."
        )
    if (
        cpmai.get("model_validation_plan_missing")
        or cpmai.get("train_validation_test_split_missing")
        or cpmai.get("drift_retraining_plan_missing")
    ):
        explanations.append(
            "CPMAI model-evaluation risk is present because validation, test strategy, drift monitoring, or retraining controls are incomplete."
        )
    if (
        cpmai.get("audit_traceability_missing")
        or cpmai.get("operational_readiness_missing")
        or cpmai.get("security_review_missing")
    ):
        explanations.append(
            "CPMAI operationalization risk is present because production readiness, auditability, or security review is incomplete."
        )

    return explanations
