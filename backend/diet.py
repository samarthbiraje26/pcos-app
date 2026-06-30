import json
import os
import random
import re
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import google.generativeai as genai

from extensions import db
from models import User, Prediction, DietPlan

diet_bp = Blueprint("diet", __name__, url_prefix="/api/diet-plan")

def extract_json_object(raw_text):
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    return match.group(0) if match else cleaned


def generate_personalized_fallback_diet(user, risk_level, last_pred):
    rng = random.SystemRandom()

    pred_inputs = {}
    if last_pred and last_pred.inputs:
        try:
            pred_inputs = json.loads(last_pred.inputs)
        except Exception:
            pred_inputs = {}

    weight = float(pred_inputs.get("weight", 60) or 60)
    bmi = float(pred_inputs.get("bmi", 23) or 23)
    regular_exercise = int(pred_inputs.get("reg_exercise", 0) or 0)
    fast_food = int(pred_inputs.get("fast_food", 0) or 0)

    base_cal = 1650 if risk_level == "Positive" else 1800
    if bmi >= 28:
        base_cal -= 120
    if regular_exercise == 1:
        base_cal += 120
    if weight < 52:
        base_cal += 80
    calories = max(1400, min(2200, int(base_cal)))

    protein = max(70, int(weight * 1.3))
    carbs = max(110, int((calories * 0.38) / 4))
    fat = max(45, int((calories - (protein * 4 + carbs * 4)) / 9))

    low_gi_breakfasts = [
        "Vegetable oats upma with chia seeds and plain curd.",
        "Besan chilla with paneer filling and mint chutney.",
        "Greek yogurt bowl with berries, flaxseeds, and a few almonds.",
        "Moong dal cheela with sauteed spinach and tomato.",
    ]
    balanced_breakfasts = [
        "Scrambled eggs with multigrain toast and cucumber slices.",
        "Peanut butter toast with fruit and unsweetened milk.",
        "Vegetable poha with roasted peanuts and curd.",
        "Idli with sambar and a side of sprouts salad.",
    ]
    lunches = [
        "Grilled protein bowl with mixed vegetables and quinoa.",
        "Dal, brown rice, sauteed vegetables, and salad.",
        "Whole-wheat roti, paneer bhurji, and cucumber raita.",
        "Chickpea salad wrap with hummus and crunchy veggies.",
    ]
    snacks = [
        "Roasted chana with buttermilk.",
        "Apple slices with peanut butter.",
        "Handful of nuts and unsweetened green tea.",
        "Carrot and cucumber sticks with hummus.",
    ]
    dinners = [
        "Baked fish/tofu with stir-fried vegetables.",
        "Millet khichdi with mixed vegetables and curd.",
        "Chicken/tofu stew with sauteed greens.",
        "Lentil soup with paneer salad.",
    ]

    breakfast_pool = low_gi_breakfasts if risk_level == "Positive" else balanced_breakfasts
    if fast_food == 1:
        avoid_seed = ["Sugary beverages", "Fried snacks", "Refined flour desserts", "Packaged fast food"]
    else:
        avoid_seed = ["High sugar drinks", "Deep-fried foods", "Excess bakery items", "Highly processed foods"]

    recommended_seed = [
        "Leafy vegetables",
        "High-fiber legumes",
        "Lean proteins",
        "Nuts and seeds",
        "Low-GI fruits",
        "Omega-3 rich foods",
    ]

    plan = {
        "today": {
            "breakfast": rng.choice(breakfast_pool),
            "lunch": rng.choice(lunches),
            "snacks": rng.choice(snacks),
            "dinner": rng.choice(dinners),
        },
        "macros": {
            "calories": calories,
            "protein": protein,
            "carb": carbs,
            "fat": fat,
        },
        "recommended": rng.sample(recommended_seed, 4),
        "avoid": avoid_seed,
        "weekly_overview": (
            f"{user.name if user and user.name else 'User'}, focus this week on consistent meal timings, "
            "protein in every major meal, and lower refined sugar intake. "
            f"Your latest screening trend is {risk_level.lower()}, so prioritize blood-sugar-friendly meals."
        ),
    }
    return plan


def ensure_plan_schema(plan_dict, fallback):
    if not isinstance(plan_dict, dict):
        return fallback

    plan = dict(plan_dict)
    plan["today"] = plan.get("today") if isinstance(plan.get("today"), dict) else fallback["today"]
    for meal_key in ["breakfast", "lunch", "snacks", "dinner"]:
        if not isinstance(plan["today"].get(meal_key), str) or not plan["today"].get(meal_key).strip():
            plan["today"][meal_key] = fallback["today"][meal_key]

    plan["macros"] = plan.get("macros") if isinstance(plan.get("macros"), dict) else fallback["macros"]
    for macro_key in ["calories", "protein", "carb", "fat"]:
        val = plan["macros"].get(macro_key)
        if not isinstance(val, (int, float)):
            plan["macros"][macro_key] = fallback["macros"][macro_key]
        else:
            plan["macros"][macro_key] = int(val)

    for list_key in ["recommended", "avoid"]:
        if not isinstance(plan.get(list_key), list) or len(plan.get(list_key, [])) < 4:
            plan[list_key] = fallback[list_key]
        else:
            plan[list_key] = [str(x) for x in plan[list_key][:4]]

    if not isinstance(plan.get("weekly_overview"), str) or not plan.get("weekly_overview").strip():
        plan["weekly_overview"] = fallback["weekly_overview"]

    return plan

@diet_bp.route("", methods=["GET"])
@jwt_required()
def get_diet_plan():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    # Check for existing plan
    existing_plan = DietPlan.query.filter_by(user_id=user_id).order_by(DietPlan.created_at.desc()).first()
    if existing_plan:
        return jsonify({"message": "Retrieved existing plan", "data": json.loads(existing_plan.plan_data)}), 200

    return generate_new_diet_plan(user_id)

@diet_bp.route("/regenerate", methods=["POST"])
@jwt_required()
def regenerate_diet_plan():
    user_id = int(get_jwt_identity())
    return generate_new_diet_plan(user_id)

def generate_new_diet_plan(user_id):
    user = User.query.get(user_id)
    # Get last prediction
    last_pred = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).first()
    risk_level = last_pred.result if last_pred else "Negative"

    # Read from environment (.env file loaded in config.py)
    api_key = os.environ.get("GEMINI_API_KEY")
    previous_plan_obj = DietPlan.query.filter_by(user_id=user_id).order_by(DietPlan.created_at.desc()).first()
    previous_plan_text = ""
    if previous_plan_obj:
        previous_plan_text = previous_plan_obj.plan_data

    fallback_plan = generate_personalized_fallback_diet(user, risk_level, last_pred)
    if not api_key:
        plan_dict = fallback_plan
    else:
        # Generate with Gemini
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-flash-latest")
            prompt = (
                "You are a clinical nutrition assistant.\n"
                "Create a one-day PCOS-friendly plan and weekly guidance in strict JSON only.\n"
                "User profile:\n"
                f"- name: {user.name if user else 'User'}\n"
                f"- age: {user.age if user and user.age else 'unknown'}\n"
                f"- latest risk trend: {risk_level}\n"
                f"- latest prediction inputs: {last_pred.inputs if last_pred else '{}'}\n"
                "Required keys exactly: today, macros, recommended, avoid, weekly_overview.\n"
                "today keys: breakfast, lunch, snacks, dinner.\n"
                "macros keys: calories, protein, carb, fat.\n"
                "recommended/avoid: arrays of exactly 4 concise strings each.\n"
                "Important: plan must differ from prior plan if one exists.\n"
                f"Previous plan JSON: {previous_plan_text if previous_plan_text else 'none'}\n"
                "Return only valid JSON without markdown."
            )
            response = model.generate_content(
                prompt, generation_config={"temperature": 1.0, "top_p": 0.95}
            )
            raw_text = extract_json_object(response.text)
            plan_dict = json.loads(raw_text)
            plan_dict = ensure_plan_schema(plan_dict, fallback_plan)
        except Exception as e:
            print("Gemini API Error:", e)
            plan_dict = fallback_plan
    
    new_plan = DietPlan(user_id=user_id, plan_data=json.dumps(plan_dict))
    db.session.add(new_plan)
    db.session.commit()

    return jsonify({"message": "Diet plan generated", "data": plan_dict}), 201
