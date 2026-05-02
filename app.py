"""Streamlit UI for the Responsible AI Risk Assessment Tool."""

from __future__ import annotations

import streamlit as st

from src.recommendations import generate_recommendations
from src.regulations import (
    CLOUD_PROVIDER_JURISDICTIONS,
    HOST_REGION_OPTIONS,
    REGION_OPTIONS,
    evaluate_regulatory_exposure,
)
from src.risk_rules import (
    PROVIDER_PROFILES,
    classify_risk_level,
    explain_detected_risks,
    get_provider_profile,
)
from src.scoring import score_assessment


st.set_page_config(
    page_title="Responsible AI Risk Assessment Tool",
    page_icon="RAI",
    layout="wide",
)


ORG_TYPES = [
    "Private sector",
    "Public sector",
    "Healthcare",
    "Financial services",
    "Education",
    "Non-profit",
    "Other",
]

USE_CASES = [
    "Customer support or operations",
    "Decision support",
    "Hiring or workforce management",
    "Healthcare or wellbeing",
    "Financial eligibility or pricing",
    "Education or assessment",
    "Public services or benefits",
    "Safety, security, or law enforcement",
    "Content generation or summarization",
    "Other",
]

MODEL_PROVIDERS = list(PROVIDER_PROFILES.keys())


def _render_header() -> None:
    """Render the application header and short positioning copy."""

    st.title("Responsible AI Risk Assessment Tool")
    st.caption(
        "A structured first-pass assessment for AI project data, model, impact, "
        "and governance risks."
    )


def _render_project_details() -> dict:
    """Collect high-level project and supplier details."""

    st.subheader("Project Details")
    left, right = st.columns(2)

    with left:
        project_name = st.text_input("Project name", placeholder="e.g. Claims Assistant")
        organization_type = st.selectbox("Organization type", ORG_TYPES)
        use_case = st.selectbox("Use case", USE_CASES)
        model_provider = st.selectbox(
            "Primary model/provider trust profile",
            MODEL_PROVIDERS,
            help="Provider defaults are based on public data-use and transparency references. Adjust the scoring rules to match your contract.",
        )

        provider_profile = get_provider_profile(model_provider)
        st.caption(f"{provider_profile['trust_label']}: {provider_profile['summary']}")

    with right:
        third_party_involved = st.radio(
            "Third-party involvement",
            ["No third party", "Supplier or vendor involved"],
            horizontal=True,
        )
        suppliers = st.text_area(
            "Suppliers",
            placeholder="List model providers, data vendors, cloud providers, or implementation partners. Leave blank if not applicable.",
        )
        model_usage_supplier = st.text_area(
            "Model usage / supplier",
            placeholder="Describe which supplier models or services are used and for what purpose. Leave blank if not applicable.",
        )

    return {
        "project_name": project_name.strip(),
        "organization_type": organization_type,
        "use_case": use_case,
        "model_provider": model_provider,
        "third_party_involved": third_party_involved == "Supplier or vendor involved",
        "suppliers": suppliers.strip(),
        "model_usage_supplier": model_usage_supplier.strip(),
    }


def _render_data_risk_inputs() -> dict:
    """Collect data-related risk factors."""

    st.subheader("Data Risk Inputs")
    col1, col2 = st.columns(2)

    with col1:
        personal_data = st.checkbox("Uses personal data")
        sensitive_data = st.checkbox(
            "Uses sensitive or special-category data",
            help="Examples include health, biometric, financial, precise location, children, or protected-class data.",
        )
        vulnerable_groups = st.checkbox("Data relates to children or vulnerable groups")

    with col2:
        external_data = st.checkbox("Uses external, scraped, or brokered data")
        data_quality_uncertain = st.checkbox("Data quality, consent, or provenance is uncertain")
        cross_border_transfer = st.checkbox("Includes cross-border data transfer")

    return {
        "personal_data": personal_data,
        "sensitive_data": sensitive_data,
        "vulnerable_groups": vulnerable_groups,
        "external_data": external_data,
        "data_quality_uncertain": data_quality_uncertain,
        "cross_border_transfer": cross_border_transfer,
    }


def _render_model_risk_inputs() -> dict:
    """Collect model-related risk factors."""

    st.subheader("Model Risk Inputs")
    col1, col2 = st.columns(2)

    with col1:
        generative_ai = st.checkbox("Uses generative AI")
        autonomous_decisions = st.checkbox("Produces automated or autonomous decisions")
        opaque_model = st.checkbox("Model behavior is difficult to explain")

    with col2:
        custom_training = st.checkbox("Model is custom trained or fine-tuned")
        continuous_learning = st.checkbox("Model changes after deployment")
        performance_untested = st.checkbox("Accuracy, robustness, or bias testing is incomplete")

    return {
        "generative_ai": generative_ai,
        "autonomous_decisions": autonomous_decisions,
        "opaque_model": opaque_model,
        "custom_training": custom_training,
        "continuous_learning": continuous_learning,
        "performance_untested": performance_untested,
    }


def _render_impact_risk_inputs() -> dict:
    """Collect impact-related risk factors."""

    st.subheader("Impact Risk Inputs")
    col1, col2 = st.columns(2)

    with col1:
        high_stakes_domain = st.checkbox("Use case affects rights, access, eligibility, safety, or livelihood")
        large_scale = st.checkbox("Deployment affects a large population")
        user_harm_possible = st.checkbox("Incorrect output could cause material harm")

    with col2:
        vulnerable_impact = st.checkbox("Potential impact on vulnerable or protected groups")
        public_facing = st.checkbox("Public-facing or customer-facing system")
        limited_human_review = st.checkbox("Limited human review before action is taken")

    return {
        "high_stakes_domain": high_stakes_domain,
        "large_scale": large_scale,
        "user_harm_possible": user_harm_possible,
        "vulnerable_impact": vulnerable_impact,
        "public_facing": public_facing,
        "limited_human_review": limited_human_review,
    }


def _render_governance_inputs() -> dict:
    """Collect governance and accountability risk factors."""

    st.subheader("Governance Inputs")
    col1, col2 = st.columns(2)

    with col1:
        no_owner = st.checkbox("No named accountable owner")
        no_documentation = st.checkbox("No model card, DPIA, AI impact assessment, or equivalent documentation")
        no_monitoring = st.checkbox("No post-deployment monitoring plan")

    with col2:
        no_incident_process = st.checkbox("No incident response or escalation process")
        no_human_oversight = st.checkbox("No defined human oversight controls")
        supplier_controls_missing = st.checkbox("Supplier due diligence or contractual controls are missing")

    return {
        "no_owner": no_owner,
        "no_documentation": no_documentation,
        "no_monitoring": no_monitoring,
        "no_incident_process": no_incident_process,
        "no_human_oversight": no_human_oversight,
        "supplier_controls_missing": supplier_controls_missing,
    }


def _render_compliance_inputs() -> dict:
    """Collect jurisdiction, hosting, and regulatory-control inputs."""

    st.subheader("Regulatory and Data Residency Inputs")
    st.caption(
        "These fields screen for likely regulatory exposure. They do not replace legal review."
    )

    location_col, control_col = st.columns(2)
    with location_col:
        organization_location = st.selectbox("Organization location", REGION_OPTIONS)
        target_regions = st.multiselect(
            "Affected user / data subject locations",
            REGION_OPTIONS,
            help="Select all locations where users, data subjects, employees, patients, or customers may be affected.",
        )
        data_host_region = st.selectbox("Primary data host location", HOST_REGION_OPTIONS)
        cloud_provider_jurisdiction = st.selectbox(
            "Cloud / hosting provider jurisdiction",
            CLOUD_PROVIDER_JURISDICTIONS,
            help="Cloud Act exposure is most relevant for US-controlled providers, even when data is stored outside the United States.",
        )
        cloud_provider_name = st.text_input(
            "Cloud / hosting provider name",
            placeholder="e.g. AWS, Azure, Google Cloud, local data center",
        )

    with control_col:
        handles_phi = st.checkbox("Handles protected health information or US healthcare data")
        handles_california_personal_information = st.checkbox(
            "Handles California residents' personal information"
        )
        handles_california_sensitive_information = st.checkbox(
            "Handles California sensitive personal information"
        )
        no_lawful_basis_or_notice = st.checkbox("Lawful basis, privacy notice, or consent path is not documented")
        no_dpia_or_transfer_assessment = st.checkbox(
            "DPIA, transfer impact assessment, or cross-border transfer mechanism is missing"
        )
        no_ai_act_classification = st.checkbox("EU AI Act risk classification has not been performed")
        no_hipaa_baa = st.checkbox("HIPAA business associate agreement or PHI safeguards are missing")
        no_consumer_rights_process = st.checkbox(
            "Consumer/data-subject rights process is missing"
        )
        no_cloud_act_review = st.checkbox(
            "Cloud Act / government-access and data-sovereignty review is missing"
        )

    return {
        "organization_location": organization_location,
        "target_regions": target_regions,
        "data_host_region": data_host_region,
        "cloud_provider_jurisdiction": cloud_provider_jurisdiction,
        "cloud_provider_name": cloud_provider_name.strip(),
        "handles_phi": handles_phi,
        "handles_california_personal_information": handles_california_personal_information,
        "handles_california_sensitive_information": handles_california_sensitive_information,
        "no_lawful_basis_or_notice": no_lawful_basis_or_notice,
        "no_dpia_or_transfer_assessment": no_dpia_or_transfer_assessment,
        "no_ai_act_classification": no_ai_act_classification,
        "no_hipaa_baa": no_hipaa_baa,
        "no_consumer_rights_process": no_consumer_rights_process,
        "no_cloud_act_review": no_cloud_act_review,
    }


def _render_cpmai_inputs() -> dict:
    """Collect CPMAI-inspired project readiness risk factors."""

    st.subheader("CPMAI Project Readiness Risks")
    st.caption(
        "Select gaps that apply. These checks reflect CPMAI themes around business understanding, "
        "data understanding, data preparation, model evaluation, and operationalization."
    )

    business_col, data_col = st.columns(2)
    with business_col:
        business_problem_unclear = st.checkbox("Business problem or decision context is unclear")
        ai_fit_unvalidated = st.checkbox("AI fit has not been validated against simpler alternatives")
        success_metrics_missing = st.checkbox("Business and technical success metrics are missing")
        roi_not_estimated = st.checkbox("Costs, benefits, or ROI have not been estimated")
        go_no_go_criteria_missing = st.checkbox("Go/no-go criteria are not defined")

    with data_col:
        data_requirements_unclear = st.checkbox("Data requirements are not clearly defined")
        data_quantity_insufficient = st.checkbox("Data quantity or coverage may be insufficient")
        ground_truth_missing = st.checkbox("Ground truth, labels, or evaluation examples are missing")
        data_access_unresolved = st.checkbox("Data access, infrastructure, or permissions are unresolved")
        pipeline_or_labeling_controls_missing = st.checkbox(
            "Data pipeline, labeling, or preparation quality controls are missing"
        )

    model_col, ops_col = st.columns(2)
    with model_col:
        model_validation_plan_missing = st.checkbox("Model validation plan is missing")
        train_validation_test_split_missing = st.checkbox("Train/validation/test split strategy is missing")
        drift_retraining_plan_missing = st.checkbox("Data drift, model drift, or retraining plan is missing")
        genai_production_controls_missing = st.checkbox("Generative AI production controls are missing")
        limits_not_defined = st.checkbox("Model limits and known failure modes are not defined")

    with ops_col:
        project_team_roles_missing = st.checkbox("AI project team roles and responsibilities are unclear")
        audit_traceability_missing = st.checkbox("Audit trail or traceability is missing")
        operational_readiness_missing = st.checkbox("Operationalization readiness is incomplete")
        security_review_missing = st.checkbox("Security, DevSecOps, or malicious-use review is missing")
        user_acceptance_change_risk = st.checkbox("User adoption, training, or change-management risk is unresolved")

    return {
        "business_problem_unclear": business_problem_unclear,
        "ai_fit_unvalidated": ai_fit_unvalidated,
        "success_metrics_missing": success_metrics_missing,
        "roi_not_estimated": roi_not_estimated,
        "go_no_go_criteria_missing": go_no_go_criteria_missing,
        "data_requirements_unclear": data_requirements_unclear,
        "data_quantity_insufficient": data_quantity_insufficient,
        "ground_truth_missing": ground_truth_missing,
        "data_access_unresolved": data_access_unresolved,
        "pipeline_or_labeling_controls_missing": pipeline_or_labeling_controls_missing,
        "model_validation_plan_missing": model_validation_plan_missing,
        "train_validation_test_split_missing": train_validation_test_split_missing,
        "drift_retraining_plan_missing": drift_retraining_plan_missing,
        "genai_production_controls_missing": genai_production_controls_missing,
        "limits_not_defined": limits_not_defined,
        "project_team_roles_missing": project_team_roles_missing,
        "audit_traceability_missing": audit_traceability_missing,
        "operational_readiness_missing": operational_readiness_missing,
        "security_review_missing": security_review_missing,
        "user_acceptance_change_risk": user_acceptance_change_risk,
    }


def _render_results(assessment: dict, scores: dict) -> None:
    """Display the final score, level, category breakdown, and guidance."""

    risk_level = classify_risk_level(scores["total"])
    explanations = explain_detected_risks(assessment, scores)
    recommendations = generate_recommendations(assessment, scores, risk_level)

    st.divider()
    st.subheader("Assessment Results")

    metric_cols = st.columns(5)
    metric_cols[0].metric("Total score", f"{scores['total']} / 100")
    metric_cols[1].metric("Risk level", risk_level)
    metric_cols[2].metric("Data", f"{scores['data']} / 30")
    metric_cols[3].metric("Model", f"{scores['model']} / 25")
    metric_cols[4].metric("Impact", f"{scores['impact']} / 30")

    st.progress(scores["total"] / 100)

    chart_data = {
        "Category": ["Data", "Model", "Impact", "Governance"],
        "Score": [
            scores["data"],
            scores["model"],
            scores["impact"],
            scores["governance"],
        ],
    }
    st.bar_chart(chart_data, x="Category", y="Score", horizontal=False)

    provider_profile = get_provider_profile(
        assessment.get("model_provider", "Internal / no external foundation model")
    )
    regulatory_exposure = evaluate_regulatory_exposure(assessment)
    with st.expander("Provider trust profile and references", expanded=False):
        st.markdown(f"**Selected profile:** {assessment.get('model_provider')}")
        st.markdown(f"**Provider:** {provider_profile['provider']}")
        st.markdown(f"**Trust label:** {provider_profile['trust_label']}")
        st.markdown(provider_profile["summary"])
        st.table(
            {
                "Risk category": ["Data", "Model", "Governance"],
                "Provider points added": [
                    provider_profile["data_risk"],
                    provider_profile["model_risk"],
                    provider_profile["governance_risk"],
                ],
            }
        )
        if provider_profile["references"]:
            st.markdown("**References**")
            for reference in provider_profile["references"]:
                st.markdown(f"- {reference}")
        st.caption(
            "These defaults are screening assumptions, not a legal conclusion or universal model safety ranking."
        )

    with st.expander("Regulatory exposure and data residency impact", expanded=True):
        exposures = regulatory_exposure["exposures"]
        if not exposures:
            st.success("No specific regulatory exposure was triggered from the selected location, data, and hosting inputs.")
        else:
            st.table(
                [
                    {
                        "Regulation": exposure["name"],
                        "Data": exposure["data_points"],
                        "Model": exposure["model_points"],
                        "Impact": exposure["impact_points"],
                        "Governance": exposure["governance_points"],
                    }
                    for exposure in exposures
                ]
            )
            for exposure in exposures:
                st.markdown(f"**{exposure['name']}**: {exposure['reason']}")
                st.markdown(f"Reference: {exposure['reference']}")
        st.caption(
            "Regulatory screening is based on selected locations, data types, use case, hosting, and missing compliance controls."
        )

    left, right = st.columns(2)
    with left:
        st.markdown("#### Explanation of Risks")
        if explanations:
            for explanation in explanations:
                st.warning(explanation)
        else:
            st.success("No major risk indicators were selected. Maintain baseline governance controls.")

    with right:
        st.markdown("#### Recommendations")
        for recommendation in recommendations:
            st.info(recommendation)


def main() -> None:
    """Run the Streamlit application."""

    _render_header()

    with st.form("risk_assessment_form"):
        project_details = _render_project_details()
        st.divider()
        data_inputs = _render_data_risk_inputs()
        st.divider()
        model_inputs = _render_model_risk_inputs()
        st.divider()
        impact_inputs = _render_impact_risk_inputs()
        st.divider()
        governance_inputs = _render_governance_inputs()
        st.divider()
        compliance_inputs = _render_compliance_inputs()
        st.divider()
        cpmai_inputs = _render_cpmai_inputs()

        submitted = st.form_submit_button("Run assessment", type="primary")

    if submitted:
        assessment = {
            **project_details,
            "data": data_inputs,
            "model": model_inputs,
            "impact": impact_inputs,
            "governance": governance_inputs,
            "compliance": compliance_inputs,
            "cpmai": cpmai_inputs,
        }
        scores = score_assessment(assessment)
        _render_results(assessment, scores)
    else:
        st.info("Complete the form and run the assessment to view risk scoring and recommendations.")


if __name__ == "__main__":
    main()
