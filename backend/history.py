"""
History & Stats Routes
-----------------------
GET    /api/history          — Paginated list of user's predictions
DELETE /api/history/<id>     — Delete one prediction record
GET    /api/stats            — Aggregate stats for the current user
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import Prediction

history_bp = Blueprint("history", __name__, url_prefix="/api")


@history_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    user_id  = get_jwt_identity()
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    paginated = (
        Prediction.query
        .filter_by(user_id=int(user_id))
        .order_by(Prediction.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "predictions":  [p.to_dict() for p in paginated.items],
        "total":        paginated.total,
        "pages":        paginated.pages,
        "current_page": page,
    }), 200


@history_bp.route("/history/<int:prediction_id>", methods=["DELETE"])
@jwt_required()
def delete_prediction(prediction_id):
    user_id = get_jwt_identity()

    prediction = Prediction.query.filter_by(
        id=prediction_id, user_id=int(user_id)
    ).first()

    if not prediction:
        return jsonify({"error": "Prediction not found"}), 404

    db.session.delete(prediction)
    db.session.commit()

    return jsonify({"message": "Prediction deleted successfully"}), 200


@history_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    user_id     = get_jwt_identity()
    predictions = (
        Prediction.query
        .filter_by(user_id=int(user_id))
        .order_by(Prediction.created_at.asc())
        .all()
    )

    total    = len(predictions)
    positive = sum(1 for p in predictions if p.result == "Positive")
    negative = total - positive
    last     = predictions[-1].to_dict() if predictions else None

    return jsonify({
        "total":           total,
        "positive":        positive,
        "negative":        negative,
        "last_prediction": last,
    }), 200
