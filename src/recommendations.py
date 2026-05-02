"""Recommendation generation for Responsible AI risk assessments."""

from __future__ import annotations

from src.regulations import evaluate_regulatory_exposure
from src.risk_rules import get_provider_profile


def generate_recommendations(assessment: dict, scores: dict, risk_level: str) -> list[str]:
    """Return practical recommendations based on detected risks."""

    recommendations = []
    data = assessment.get("data", {})
    model = assessment.get("model", {})
    impact = assessment.get("impact", {})
    governance = assessment.get("governance", {})
    cpmai = assessment.get("cpmai", {})
    provider_profile = get_provider_profile(
        assessment.get("model_provider", "Internal / no external foundation model")
    )
    regulatory_exposure = evaluate_regulatory_exposure(assessment)
    exposure_names = {exposure["name"] for exposure in regulatory_exposure["exposures"]}

    if risk_level in {"High", "Critical"}:
        recommendations.append(
            "Require senior approval before deployment and maintain an auditable risk decision record."
        )
    if risk_level == "Critical":
        recommendations.append(
            "Pause production launch until high-risk controls are implemented and independently reviewed."
        )
    if "EU AI Act" in exposure_names:
        recommendations.append(
            "Perform EU AI Act classification and document provider/deployer obligations, human oversight, transparency, logging, accuracy, robustness, cybersecurity, and fundamental-rights impact controls."
        )
    if "GDPR" in exposure_names or "UK GDPR" in exposure_names:
        recommendations.append(
            "Confirm lawful basis, transparency notices, data minimization, retention, data-subject rights, DPIA needs, processor contracts, and cross-border transfer safeguards."
        )
    if "HIPAA" in exposure_names:
        recommendations.append(
            "Confirm HIPAA covered-entity/business-associate status, execute BAAs with vendors that handle ePHI, and document administrative, physical, and technical safeguards."
        )
    if "CCPA / CPRA" in exposure_names:
        recommendations.append(
            "Prepare California privacy disclosures, consumer-rights intake, correction/deletion/opt-out handling, sensitive personal information controls, and service-provider contract terms."
        )
    if "Singapore PDPA" in exposure_names or "Thailand PDPA" in exposure_names:
        recommendations.append(
            "Confirm local PDPA requirements for notice, consent or lawful basis, purpose limitation, security, breach response, cross-border transfer, and data-subject rights."
        )
    if "US CLOUD Act" in exposure_names:
        recommendations.append(
            "Review Cloud Act and data-sovereignty exposure: provider jurisdiction, data residency, encryption/key control, government-access process, customer notification, and contractual challenge rights."
        )
    if cpmai.get("business_problem_unclear") or cpmai.get("ai_fit_unvalidated"):
        recommendations.append(
            "Run a CPMAI-style business-understanding review: define the problem, compare AI with simpler alternatives, and document the go/no-go decision."
        )
    if cpmai.get("success_metrics_missing") or cpmai.get("roi_not_estimated"):
        recommendations.append(
            "Define measurable business and technical success metrics, acceptable performance levels, cost assumptions, and expected benefits."
        )

    if scores.get("data", 0) >= 10:
        recommendations.append(
            "Complete a data protection and provenance review covering lawful basis, consent, minimization, retention, and access."
        )
    if cpmai.get("data_requirements_unclear") or cpmai.get("data_access_unresolved"):
        recommendations.append(
            "Document data requirements, source systems, access permissions, infrastructure dependencies, and data ownership before development."
        )
    if cpmai.get("data_quantity_insufficient") or cpmai.get("ground_truth_missing"):
        recommendations.append(
            "Confirm whether available data volume, coverage, labels, and ground-truth examples are sufficient for training and evaluation."
        )
    if data.get("sensitive_data") or data.get("vulnerable_groups"):
        recommendations.append(
            "Apply enhanced safeguards for sensitive or vulnerable-group data, including stricter access controls and documented necessity."
        )
    if data.get("data_quality_uncertain"):
        recommendations.append(
            "Validate data quality, representativeness, bias, consent, and lineage before model development or deployment."
        )
    if provider_profile["data_risk"] >= 4:
        recommendations.append(
            "Do not submit personal, sensitive, confidential, or regulated data until provider data-use, retention, review, and opt-out terms are contractually confirmed."
        )
    if cpmai.get("pipeline_or_labeling_controls_missing"):
        recommendations.append(
            "Create data preparation controls for ingestion, cleansing, sampling, labeling quality, augmentation, and repeatable training/inference pipelines."
        )

    if scores.get("model", 0) >= 10:
        recommendations.append(
            "Create a model evaluation plan covering accuracy, robustness, bias, security, explainability, and failure modes."
        )
    if cpmai.get("model_validation_plan_missing") or cpmai.get("train_validation_test_split_missing"):
        recommendations.append(
            "Define model validation gates, train/validation/test split strategy, benchmark data, and acceptance thresholds before release."
        )
    if cpmai.get("drift_retraining_plan_missing"):
        recommendations.append(
            "Define data drift, model drift, monitoring KPIs, retraining triggers, rollback criteria, and ownership for ongoing oversight."
        )
    if model.get("generative_ai"):
        recommendations.append(
            "Add controls for hallucination, prompt injection, unsafe content, sensitive data leakage, and human review of consequential outputs."
        )
    if cpmai.get("genai_production_controls_missing"):
        recommendations.append(
            "For generative AI, add production controls for retrieval quality, prompt injection, content filtering, logging, red-team testing, and human review."
        )
    if model.get("continuous_learning"):
        recommendations.append(
            "Define change management, drift monitoring, rollback criteria, and re-validation triggers for model updates."
        )

    if scores.get("impact", 0) >= 10:
        recommendations.append(
            "Run an AI impact assessment that evaluates affected groups, foreseeable harms, appeal routes, and mitigation effectiveness."
        )
    if impact.get("high_stakes_domain") or impact.get("user_harm_possible"):
        recommendations.append(
            "Keep a meaningful human-in-the-loop process for consequential decisions, with authority to override model output."
        )
    if impact.get("large_scale") or impact.get("public_facing"):
        recommendations.append(
            "Prepare user notices, feedback channels, monitoring dashboards, and incident communications before rollout."
        )
    if cpmai.get("limits_not_defined") or cpmai.get("user_acceptance_change_risk"):
        recommendations.append(
            "Document model limitations, unsupported use cases, user training needs, adoption risks, and escalation paths."
        )

    if scores.get("governance", 0) >= 5:
        recommendations.append(
            "Assign an accountable owner and maintain documentation for model purpose, limitations, controls, approvals, and monitoring."
        )
    if cpmai.get("project_team_roles_missing") or cpmai.get("go_no_go_criteria_missing"):
        recommendations.append(
            "Clarify AI project roles, responsibilities, approval gates, and go/no-go criteria for each delivery phase."
        )
    if cpmai.get("audit_traceability_missing") or cpmai.get("operational_readiness_missing"):
        recommendations.append(
            "Prepare operationalization evidence, audit trail, deployment plan, monitoring dashboard, support model, and lifecycle ownership."
        )
    if cpmai.get("security_review_missing"):
        recommendations.append(
            "Complete security and DevSecOps review covering model endpoints, data pipelines, abuse cases, access control, and incident response."
        )
    if governance.get("no_incident_process"):
        recommendations.append(
            "Define an AI incident response process with severity levels, escalation owners, containment actions, and post-incident review."
        )
    if assessment.get("third_party_involved"):
        recommendations.append(
            "Perform supplier due diligence covering data use, security, audit rights, subcontractors, service levels, and exit plans."
        )
    if provider_profile["governance_risk"] >= 3:
        recommendations.append(
            "Require supplier evidence for model safety testing, incident handling, data retention, subprocessors, and audit rights before production use."
        )

    if not recommendations:
        recommendations.append(
            "Maintain baseline responsible AI controls, document assumptions, and reassess when the project scope changes."
        )

    return recommendations
