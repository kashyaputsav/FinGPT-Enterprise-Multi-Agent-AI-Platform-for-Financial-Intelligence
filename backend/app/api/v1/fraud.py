from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.schemas import FraudCheckRequest, FraudCheckResponse
from app.models.user import User
from app.services.fraud_service import score_transaction

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.post("/check", response_model=FraudCheckResponse)
async def check_transaction(
    payload: FraudCheckRequest,
    current_user: User = Depends(get_current_user),
):
    """Quantitative fraud risk score (XGBoost + SHAP attribution)."""
    return await score_transaction(payload)
