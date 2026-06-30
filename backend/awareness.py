"""
PCOS Awareness Blueprint
─────────────────────────
Serves curated educational content about PCOS alongside
Gemini-personalized lifestyle tips.
"""
import json
import os
import random
import re
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import google.generativeai as genai

from extensions import db
from models import User, Prediction, AwarenessTip

awareness_bp = Blueprint("awareness", __name__, url_prefix="/api/awareness")

# ── Static curated content ──────────────────────────────────────────────────

WHAT_IS_PCOS = {
    "title": "What is PCOS?",
    "description": (
        "Polycystic Ovary Syndrome (PCOS) is a common hormonal disorder that affects "
        "people with ovaries, typically during their reproductive years. It is characterized "
        "by irregular menstrual cycles, excess androgen levels, and polycystic ovaries."
    ),
    "key_stats": [
        "Affects approximately 1 in 10 people of reproductive age worldwide.",
        "It is one of the most common causes of infertility.",
        "Up to 70% of affected individuals remain undiagnosed.",
        "Early detection and lifestyle changes can significantly improve outcomes.",
    ],
}

SYMPTOMS = [
    {"icon": "🔄", "name": "Irregular Periods",       "desc": "Infrequent, irregular, or prolonged menstrual cycles are a hallmark sign of PCOS."},
    {"icon": "⚖️", "name": "Weight Fluctuation",      "desc": "Unexplained weight gain, especially around the abdomen, due to insulin resistance."},
    {"icon": "🧴", "name": "Acne & Oily Skin",        "desc": "Hormonal imbalances can cause persistent acne on the face, chest, and back."},
    {"icon": "💇", "name": "Hair Thinning",            "desc": "Hair loss or thinning on the scalp, similar to male-pattern baldness."},
    {"icon": "🌱", "name": "Excess Hair Growth",       "desc": "Hirsutism — unwanted hair growth on the face, chin, chest, or other areas."},
    {"icon": "😴", "name": "Fatigue & Mood Changes",   "desc": "Chronic fatigue, mood swings, anxiety, or depression linked to hormonal shifts."},
    {"icon": "🍫", "name": "Cravings & Hunger",        "desc": "Intense sugar cravings and increased appetite driven by insulin resistance."},
    {"icon": "🌙", "name": "Sleep Disturbances",       "desc": "Sleep apnea and poor sleep quality are more common in individuals with PCOS."},
]

CAUSES = [
    {"title": "Insulin Resistance",      "desc": "The body's cells don't respond effectively to insulin, leading to higher blood sugar and excess insulin production."},
    {"title": "Hormonal Imbalance",      "desc": "Elevated androgens (male hormones) disrupt normal ovarian function and egg development."},
    {"title": "Genetics",                "desc": "PCOS often runs in families. Having a close relative with PCOS increases your risk."},
    {"title": "Chronic Inflammation",    "desc": "Low-grade inflammation in the body stimulates polycystic ovaries to produce excess androgens."},
    {"title": "Lifestyle Factors",       "desc": "Sedentary lifestyle, poor diet, chronic stress, and lack of sleep can worsen or trigger PCOS symptoms."},
]

MYTHS_VS_FACTS = [
    {"myth": "PCOS only affects overweight people.",
     "fact": "PCOS can affect anyone regardless of body weight. Lean PCOS is a recognized condition."},
    {"myth": "You can't get pregnant if you have PCOS.",
     "fact": "Many people with PCOS conceive naturally or with medical support. It's manageable, not a sentence."},
    {"myth": "PCOS will go away on its own.",
     "fact": "PCOS is a chronic condition that requires ongoing management through lifestyle and sometimes medication."},
    {"myth": "PCOS is just about irregular periods.",
     "fact": "PCOS is a metabolic and hormonal disorder affecting the entire body — skin, weight, mood, fertility, and more."},
    {"myth": "Birth control pills cure PCOS.",
     "fact": "Oral contraceptives can help manage symptoms but do not address the root hormonal and metabolic imbalances."},
    {"myth": "Diet and exercise don't really matter.",
     "fact": "Lifestyle modifications are considered the first-line treatment and can dramatically improve symptoms and lab values."},
]

WHEN_TO_SEE_DOCTOR = [
    "You've missed periods or have very irregular cycles for 3+ months.",
    "You notice sudden or unexplained weight gain.",
    "You experience excess facial or body hair growth.",
    "You have persistent acne that doesn't respond to standard treatments.",
    "You are trying to conceive and having difficulty.",
    "You feel persistent fatigue, anxiety, or mood changes without clear cause.",
]


# ── Personalized fallback tips ──────────────────────────────────────────────

def _generate_fallback_tips(risk_level, user=None):
    """Return 6 actionable lifestyle tips based on risk level."""
    rng = random.SystemRandom()

    positive_pool = [
        "Prioritize low-GI carbohydrates like oats, millets, and lentils at every meal.",
        "Include 30 minutes of moderate exercise (brisk walking, yoga, swimming) most days.",
        "Reduce refined sugar and processed food intake to improve insulin sensitivity.",
        "Add anti-inflammatory spices like turmeric, cinnamon, and ginger to your diet.",
        "Practice stress management daily — deep breathing, meditation, or journaling.",
        "Aim for 7-8 hours of quality sleep with consistent bed and wake times.",
        "Stay hydrated with at least 2-3 liters of water per day.",
        "Include omega-3 rich foods like flaxseeds, walnuts, and fatty fish weekly.",
        "Track your menstrual cycle and symptoms to spot patterns over time.",
        "Consider strength training 2-3 times per week to improve metabolic health.",
    ]

    negative_pool = [
        "Maintain a balanced diet with diverse whole foods to support overall health.",
        "Stay physically active with at least 150 minutes of moderate exercise per week.",
        "Keep stress levels in check through regular relaxation and downtime.",
        "Continue regular health check-ups and screenings as recommended.",
        "Prioritize sleep hygiene — consistent schedules and a dark, cool bedroom.",
        "Include fiber-rich foods and lean proteins for sustained energy.",
        "Stay informed about hormonal health and track any changes in your cycle.",
        "Limit alcohol and caffeine intake for better hormonal balance.",
        "Practice mindful eating to develop a healthier relationship with food.",
        "Stay connected with a support community for motivation and accountability.",
    ]

    pool = positive_pool if risk_level == "Positive" else negative_pool
    tips = rng.sample(pool, min(6, len(pool)))

    if user and user.name:
        tips[0] = f"{user.name}, {tips[0][0].lower()}{tips[0][1:]}"

    return tips


def _extract_tips_json(raw_text):
    """Best-effort extraction of a JSON array from Gemini output."""
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        return match.group(0)
    return cleaned


# ── Routes ──────────────────────────────────────────────────────────────────

@awareness_bp.route("", methods=["GET"])
@jwt_required()
def get_awareness():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    last_pred = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).first()
    risk_level = last_pred.result if last_pred else "Negative"

    # Try to get cached tips
    cached = AwarenessTip.query.filter_by(user_id=user_id).order_by(AwarenessTip.created_at.desc()).first()
    if cached:
        tips = json.loads(cached.tips_data)
    else:
        tips = _generate_tips(user, risk_level)
        new_entry = AwarenessTip(user_id=user_id, tips_data=json.dumps(tips))
        db.session.add(new_entry)
        db.session.commit()

    payload = {
        "what_is_pcos":        WHAT_IS_PCOS,
        "symptoms":            SYMPTOMS,
        "causes":              CAUSES,
        "myths_vs_facts":      MYTHS_VS_FACTS,
        "when_to_see_doctor":  WHEN_TO_SEE_DOCTOR,
        "lifestyle_tips":      tips,
        "risk_level":          risk_level,
    }
    return jsonify({"message": "Awareness data loaded", "data": payload}), 200


@awareness_bp.route("/refresh-tips", methods=["POST"])
@jwt_required()
def refresh_tips():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    last_pred = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).first()
    risk_level = last_pred.result if last_pred else "Negative"

    tips = _generate_tips(user, risk_level)

    new_entry = AwarenessTip(user_id=user_id, tips_data=json.dumps(tips))
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"message": "Tips refreshed", "data": {"lifestyle_tips": tips}}), 201


def _generate_tips(user, risk_level):
    """Generate lifestyle tips via Gemini or fall back to curated content."""
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return _generate_fallback_tips(risk_level, user)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        prompt = (
            "You are a women's health lifestyle coach.\n"
            "Generate exactly 6 concise, actionable PCOS lifestyle tips as a JSON array of strings.\n"
            f"The user's name is {user.name if user else 'User'} "
            f"(age: {user.age if user and user.age else 'unknown'}).\n"
            f"Their latest PCOS screening trend is: {risk_level}.\n"
            "Tips should cover diet, exercise, sleep, stress, and self-care.\n"
            "Personalize the first tip using the user's name.\n"
            "Return ONLY a valid JSON array, no markdown wrapping."
        )
        response = model.generate_content(
            prompt, generation_config={"temperature": 1.0, "top_p": 0.95}
        )
        raw = _extract_tips_json(response.text)
        tips = json.loads(raw)
        if isinstance(tips, list) and len(tips) >= 4:
            return [str(t) for t in tips[:6]]
        return _generate_fallback_tips(risk_level, user)
    except Exception as e:
        print("Gemini Awareness Error:", e)
        return _generate_fallback_tips(risk_level, user)
