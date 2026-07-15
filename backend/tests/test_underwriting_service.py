import pytest

from app.models.schemas import LoanApplicationRequest
from app.services.underwriting_service import evaluate_application


@pytest.mark.asyncio
async def test_high_credit_low_debt_approves():
    payload = LoanApplicationRequest(
        applicant_name="Jane Doe",
        annual_income=1_500_000,
        credit_score=780,
        loan_amount=200_000,
        loan_purpose="home_improvement",
        existing_debt=50_000,
    )
    result = await evaluate_application(payload)
    assert result.decision in {"approved", "manual_review"}
    assert 0 <= result.confidence <= 1


@pytest.mark.asyncio
async def test_low_credit_rejects():
    payload = LoanApplicationRequest(
        applicant_name="John Roe",
        annual_income=400_000,
        credit_score=550,
        loan_amount=500_000,
        loan_purpose="personal",
        existing_debt=300_000,
    )
    result = await evaluate_application(payload)
    assert result.decision == "rejected"
