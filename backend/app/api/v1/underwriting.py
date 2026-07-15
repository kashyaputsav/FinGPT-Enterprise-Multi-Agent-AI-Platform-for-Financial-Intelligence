from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.schemas import LoanApplicationRequest, LoanDecisionResponse
from app.models.user import User
from app.services.underwriting_service import evaluate_application

router = APIRouter(prefix="/underwriting", tags=["underwriting"])


@router.post("/evaluate", response_model=LoanDecisionResponse)
async def evaluate_loan(
    payload: LoanApplicationRequest,
    current_user: User = Depends(get_current_user),
):
    return await evaluate_application(payload)
