# app/routes/chat_routes.py

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.models import db, ChatMessage
from app.services.fixtures import find_current_round

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=["GET"])
@login_required
def chat():
    round_number = find_current_round()
    chat_messages = []
    if round_number:
        chat_messages = (
            ChatMessage.query.filter_by(round_number=round_number)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )

    return render_template(
        "chat.html",
        round_number=round_number,
        chat_messages=chat_messages,
        chat_open=bool(round_number),
    )

@chat_bp.route('/chat/post_message', methods=["POST"])
@login_required
def post_message():
    round_number = request.form.get("round_number", type=int) or find_current_round()
    message = request.form.get("message", "").strip()

    if not round_number:
        return jsonify({"error": "Chat is unavailable until fixtures are loaded."}), 400
    if message:
        new_msg = ChatMessage(
            user_id=current_user.id,
            round_number=round_number,
            message=message,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_msg)
        db.session.commit()
        
        avatar_url = f"/static/avatars/{current_user.avatar}"
        return jsonify({
            "username": current_user.username,
            "avatar": avatar_url,
            "message": new_msg.message,
            "timestamp": new_msg.timestamp.strftime("%H:%M")
        })

    return jsonify({"error": "Empty message."}), 400

@chat_bp.route('/chat/messages')
@login_required
def get_messages():
    round_number = request.args.get("round_number", type=int) or find_current_round()
    if not round_number:
        return jsonify({"error": "Chat is unavailable until fixtures are loaded."}), 400

    messages = ChatMessage.query.filter_by(round_number=round_number).order_by(ChatMessage.timestamp.asc()).all()
    
    result = [{
        "username": msg.user.username,
        "avatar": f"/static/avatars/{msg.user.avatar}",
        "message": msg.message,
        "timestamp": msg.timestamp.strftime("%H:%M")
    } for msg in messages]

    return jsonify({"messages": result})
