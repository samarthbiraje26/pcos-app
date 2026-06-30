"""
Prediction Route
----------------
POST /api/predict  — Accept feature inputs, run model, save & return result
"""
import json

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Prediction
from ml_model import get_model

predict_bp = Blueprint("predict", __name__, url_prefix="/api")

# All 22 features expected by the XGBoost model
REQUIRED_FIELDS = [
    # Personal metrics
    "age", "weight", "height", "bmi",
    "blood_group", "pulse_rate",
    # Cycle & history
    "cycle_type", "cycle_length",
    "marriage_years", "pregnant", "vitamin_d3",
    # Symptoms
    "skin_darkening", "pimples", "weight_gain",
    "hair_growth", "hair_loss", "fast_food", "reg_exercise",
    # Ultrasound
    "follicle_left", "follicle_right",
    "avg_fsize_left", "avg_fsize_right",
]


@predict_bp.route("/predict", methods=["POST"])
@jwt_required()
def predict():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "No input data provided"}), 400

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    model = get_model()
    prediction_result = model.predict(data)

    prediction = Prediction(
        user_id=int(user_id),
        inputs=json.dumps(data),
        result=prediction_result["result"],
        confidence=prediction_result["confidence"],
    )
    db.session.add(prediction)
    db.session.commit()

    return jsonify({
        "prediction_id": prediction.id,
        "result":        prediction_result["result"],
        "confidence":    prediction_result["confidence"],
        "message":       "Prediction completed successfully",
    }), 200
