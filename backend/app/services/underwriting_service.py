"""
Loan underwriting decision engine — a transparent, rules-plus-model hybrid.
Replace `_risk_model_score` with your trained model (LightGBM/XGBoost) for
production use; the rule layer stays as a compliance guardrail regardless.
"""
from app.models.schemas import LoanApplicationRequest, LoanDecisionResponse


def _debt_to_income(payload: LoanApplicationRequest) -> float:
    if payload.annual_income <= 0:
        return float("inf")
    return (payload.existing_debt + payload.loan_amount * 0.1) / payload.annual_income


def _risk_model_score(payload: LoanApplicationRequest) -> float:
    """
    Placeholder scoring function combining credit score and DTI into a single
    0-1 confidence score. Swap for a trained model's `predict_proba` call.
    """
    credit_component = (payload.credit_score - 300) / 600  # normalize 300-900 -> 0-1
    dti = _debt_to_income(payload)
    dti_component = max(0.0, 1 - dti)
    return round(0.6 * credit_component + 0.4 * dti_component, 3)


async def evaluate_application(payload: LoanApplicationRequest) -> LoanDecisionResponse:
    score = _risk_model_score(payload)
    dti = _debt_to_income(payload)

    conditions: list[str] = []

    if payload.credit_score < 600 or dti > 0.5:
        decision = "rejected"
        rationale = (
            f"Credit score ({payload.credit_score}) or debt-to-income ratio "
            f"({dti:.2f}) falls outside acceptable lending policy thresholds."
        )
    elif score >= 0.7:
        decision = "approved"
        rationale = f"Composite risk score of {score} meets the auto-approval threshold (>=0.7)."
    else:
        decision = "manual_review"
        rationale = f"Composite risk score of {score} falls in the manual-review band (0.5-0.7)."
        conditions.append("Requires human underwriter sign-off before disbursal")

    if dti > 0.35:
        conditions.append("Consider requesting proof of additional income sources")

    return LoanDecisionResponse(decision=decision, confidence=score, rationale=rationale, conditions=conditions)
