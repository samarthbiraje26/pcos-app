"""
PCOSense Chatbot API Blueprint
------------------------------
A clinical chatbot helper powered by Google Gemini (gemini-2.0-flash),
fully personalized with user profile details and PCOS assessment history.
"""
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import google.generativeai as genai

from extensions import db
from models import ChatHistory, User, Prediction

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


# ── Chat Helpers ──────────────────────────────────────────────────────────────

def get_personalization_context(user_id):
    """Retrieves user info and prediction history to build a personalized system prompt."""
    user = User.query.get(user_id)
    last_pred = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).first()

    name = user.name if user else "User"
    context_str = f"User Name: {name}"
    
    if user and user.age:
        context_str += f", Age: {user.age}"
        
    if last_pred:
        context_str += f", Latest PCOS Assessment Result: {last_pred.result} (with {int(last_pred.confidence * 100)}% confidence)"
    else:
        context_str += ", Latest PCOS Assessment: None (no tests completed yet)"
        
    return name, context_str


# ── Chat Entrypoints ──────────────────────────────────────────────────────────

@chat_bp.route("/send", methods=["POST"])
@jwt_required()
def send_chat_message():
    user_id = int(get_jwt_identity())
    msg_text = request.json.get("message", "").strip()

    if not msg_text:
        return jsonify({"error": "Message content is required"}), 400

    # 1. Save user's message to Database
    user_msg_record = ChatHistory(user_id=user_id, role="user", message=msg_text)
    db.session.add(user_msg_record)
    db.session.commit()

    # 2. Get API Key and Personalization Info
    api_key = os.environ.get("GEMINI_API_KEY")
    user_name, user_context = get_personalization_context(user_id)

    # 3. Construct System Prompt
    system_instruction = (
        "You are PCOSense AI, a warm, professional, and compassionate health assistant specializing in "
        "Polycystic Ovary Syndrome (PCOS). Your goal is to guide, inform, and support the user regarding "
        "PCOS symptoms, lifestyle habits, diet, exercise, and overall health.\n\n"
        "Active User Context:\n"
        f"{user_context}\n\n"
        "Guidelines:\n"
        f"1. Address the user friendly and supportively (e.g., greet them as {user_name} if appropriate).\n"
        "2. Provide highly structured, clear, and reassuring resources/answers. Use simple bullet points or lists in markdown.\n"
        "3. Always include a disclaimer when providing symptom-related advice: remind them that you are an informational AI assistant, "
        "not a clinical doctor, and that they should see a doctor for formal diagnosis or medical decisions.\n"
        "4. Restrict discussions to health, PCOS, lifestyle, diet, symptoms, wellness, or supportive greetings. "
        "If a user asks about completely unrelated topics (like programming, politics, or general trivia), politely remind them that "
        "your function is specifically focused on assisting them with PCOS and health management.\n"
        "5. Keep responses concise so they are pleasant to read inside the chat box."
    )

    bot_text = ""

    if not api_key:
        # Fallback if no Gemini configuration is available
        bot_text = (
            f"Hello {user_name}, I'm currently running in limited status because my AI configuration is not available. "
            "PCOS (Polycystic Ovary Syndrome) management typically focuses on a healthy low-GI diet, stress relief, "
            "sufficient sleep, and regular physical workouts. Please consult a healthcare professional for clinical advice."
        )
    else:
        try:
            # Configure API
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-flash-latest",
                system_instruction=system_instruction
            )

            # Build conversation history context (limit to last 10 messages for optimization)
            past_messages = (
                ChatHistory.query
                .filter_by(user_id=user_id)
                .order_by(ChatHistory.created_at.desc())
                .limit(10)
                .all()
            )
            past_messages.reverse()

            chat_history = []
            for msg in past_messages[:-1]: # Exclude the user message we just saved since send_message submits it
                chat_history.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [msg.message]
                })

            # Start chat session with history context
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(msg_text)
            bot_text = response.text

        except Exception as e:
            # Fallback error messaging to ensure user experience does not fail
            print(f"[PCOSense AI Error] {repr(e)}")
            bot_text = (
                "Main service is experiencing high load or connection issues right now. "
                "PCOS management usually involves balancing insulin levels with healthy foods and routine exercise. "
                "Please remember to consult a certified gynaecologist or healthcare professional for diagnosis."
            )

    # 4. Save Bot's response to Database
    bot_msg_record = ChatHistory(user_id=user_id, role="assistant", message=bot_text)
    db.session.add(bot_msg_record)
    db.session.commit()

    return jsonify({
        "data": {
            "role": "assistant",
            "message": bot_text
        }
    }), 201


@chat_bp.route("/history", methods=["GET"])
@jwt_required()
def get_chat_history():
    user_id = int(get_jwt_identity())
    history = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.created_at.asc()).all()
    return jsonify({"data": [h.to_dict() for h in history]}), 200


@chat_bp.route("/clear", methods=["POST"])
@jwt_required()
def clear_chat_history():
    user_id = int(get_jwt_identity())
    ChatHistory.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({"message": "Chat history cleared successfully"}), 200