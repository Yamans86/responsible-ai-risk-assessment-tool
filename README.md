# Responsible AI Risk Assessment Tool

A Streamlit web app for performing a structured first-pass risk assessment of AI projects. The tool captures project context, data risks, model risks, impact risks, governance controls, and third-party supplier involvement, then produces a score, risk classification, explanatory notes, and practical recommendations.

## Features

- Structured project intake form
- Data, model, impact, and governance scoring
- Provider/model trust profile scoring for OpenAI, Gemini, Claude, Azure OpenAI, self-hosted models, and unknown suppliers
- CPMAI-inspired project readiness checks across business understanding, data understanding, data preparation, model evaluation, and operationalization
- Total score out of 100
- Risk levels: Low, Moderate, High, Critical
- Category breakdown chart
- Risk explanations based on selected indicators
- Recommendations for governance, privacy, testing, oversight, and supplier controls

## Project Structure

```text
.
|-- app.py
|-- requirements.txt
|-- README.md
|-- run_app.ps1
`-- src
    |-- __init__.py
    |-- recommendations.py
    |-- risk_rules.py
    `-- scoring.py
```

## Running the App

Install dependencies:

```bash
pip install -r requirements.txt
```

Start Streamlit:

```bash
streamlit run app.py
```

On Windows, this repository also includes a convenience launcher:

```powershell
.\run_app.ps1
```

## Methodology

The tool uses a points-based assessment across four categories:

| Category | Maximum score |
| --- | ---: |
| Data risk | 30 |
| Model risk | 25 |
| Impact risk | 30 |
| Governance risk | 15 |
| Total | 100 |

Each selected risk indicator contributes a predefined weight. Third-party supplier involvement contributes to governance risk, and missing supplier names or model-usage descriptions add further governance points because they reduce auditability and accountability.

The tool also includes provider trust profiles. These profiles add points across data, model, and governance risk based on public data-use commitments and transparency signals. For example, paid/API enterprise services with published "not used for training by default" commitments receive lower data-sharing risk points than unknown providers or unpaid services where content may be used for product or model improvement.

The tool includes additional CPMAI-inspired readiness checks derived from the supplied CPMAI course modules:

- Business understanding: problem clarity, AI fit, success metrics, ROI, go/no-go criteria
- Data understanding: requirements, quantity, access, infrastructure, labels, and ground truth
- Data preparation: pipelines, cleansing, sampling, labeling quality, and repeatable preparation controls
- Model development and evaluation: validation plans, train/validation/test strategy, drift, retraining, and generative AI controls
- Operationalization: audit trails, production readiness, lifecycle ownership, security, and change management

The category score is capped at its maximum, and the total score is classified as:

| Total score | Risk level |
| ---: | --- |
| 0-24 | Low |
| 25-49 | Moderate |
| 50-74 | High |
| 75-100 | Critical |

The weighting is intentionally transparent and easy to adjust in `src/scoring.py`.

## Provider Trust Profile Sources

The provider profiles are screening assumptions based on public references. They are not a universal safety ranking and should be adjusted to match your contract, region, deployment architecture, and data processing terms.

- OpenAI API data controls: https://platform.openai.com/docs/models/how-we-use-your-data
- OpenAI business data privacy: https://openai.com/index/business-data
- Google Gemini API terms for paid and unpaid services: https://ai.google.dev/gemini-api/terms_preview
- Google Gemini API data logging policy: https://ai.google.dev/gemini-api/docs/logs-policy
- Azure OpenAI data privacy: https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy
- Anthropic commercial data processor guidance: https://support.anthropic.com/en/articles/9267385-does-anthropic-act-as-a-data-processor-or-controller
- Stanford Foundation Model Transparency Index: https://github.com/stanford-crfm/fmti

## Limitations

This tool is a screening aid, not a legal, regulatory, privacy, security, or ethics determination. It does not replace expert review, data protection impact assessments, security assessments, model evaluations, procurement due diligence, or jurisdiction-specific compliance analysis.

Scores depend on the accuracy of user inputs. Organizations should calibrate the weights and thresholds to match their internal risk framework, applicable laws, industry standards, and risk appetite.

## Suggested Use

Use this tool during project intake, design review, procurement review, pre-launch approval, and periodic reassessment. For High or Critical results, require additional review before deployment.
