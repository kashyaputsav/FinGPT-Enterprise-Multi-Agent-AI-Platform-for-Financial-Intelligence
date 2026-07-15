"""
Quantitative fraud scoring service.

In production this loads the trained XGBoost model artifact (see
`docs/ARCHITECTURE.md` for the training pipeline: SMOTE-balanced training data,
SHAP for feature attribution, 93% precision / 85% recall on the held-out set)
from S3 at startup. Swap `_load_model` to point at your model registry
(S3 / SageMaker Model Registry / MLflow).
"""
import functools
from pathlib import Path

import numpy as np
import shap
import xgboost as xgb

from app.core.logging import get_logger
from app.models.schemas import FraudCheckRequest, FraudCheckResponse

logger = get_logger(__name__)

FEATURE_NAMES = ["amount", "hour_of_day", "merchant_risk_score", "distance_from_home_km", "velocity_1h"]

MODEL_PATH = Path(__file__).resolve().parents[1] / "ml_artifacts" / "fraud_xgb_model.json"


@functools.lru_cache
def _load_model() -> xgb.XGBClassifier | None:
    if not MODEL_PATH.exists():
        logger.warning("fraud_model_not_found", path=str(MODEL_PATH))
        return None
    model = xgb.XGBClassifier()
    model.load_model(str(MODEL_PATH))
    return model


def _engineer_features(payload: FraudCheckRequest) -> np.ndarray:
    """Placeholder feature engineering — replace with the real feature pipeline."""
    return np.array(
        [[
            payload.amount,
            12.0,  # hour_of_day — derive from transaction timestamp in production
            0.5,  # merchant_risk_score — looked up from a merchant risk table
            0.0,  # distance_from_home_km — derived from device/geo signals
            1.0,  # velocity_1h — transaction count in the trailing hour
        ]]
    )


async def score_transaction(payload: FraudCheckRequest) -> FraudCheckResponse:
    model = _load_model()
    features = _engineer_features(payload)

    if model is None:
        # Graceful degradation when no model artifact is deployed yet.
        return FraudCheckResponse(
            transaction_id=payload.transaction_id,
            risk_score=0.0,
            is_flagged=False,
            reasons=["No fraud model artifact deployed — this is a stub response."],
            shap_top_features=[],
        )

    risk_score = float(model.predict_proba(features)[0][1])
    is_flagged = risk_score >= 0.5

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(features)
    top_features = sorted(
        zip(FEATURE_NAMES, shap_values[0]), key=lambda x: abs(x[1]), reverse=True
    )[:3]

    return FraudCheckResponse(
        transaction_id=payload.transaction_id,
        risk_score=risk_score,
        is_flagged=is_flagged,
        reasons=(
            ["Risk score exceeds the 0.5 flagging threshold"] if is_flagged else ["Within normal risk range"]
        ),
        shap_top_features=[{"feature": f, "impact": float(v)} for f, v in top_features],
    )
