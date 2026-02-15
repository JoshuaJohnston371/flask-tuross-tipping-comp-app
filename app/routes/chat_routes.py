# app/routes/chat_routes.py

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from app.models import db, FixtureFree, ChatMessage
from app.services.fixtures import find_current_round
import pytz

chat_bp = Blueprint('chat', __name__)
au_tz = pytz.timezone("Australia/Sydney")

def is_chat_open(match):
    """Returns True if chat is open (30 mins before kickoff to midnight of match day)."""
    if not match or not match.time:
        return False

    datetime_now = datetime.now(au_tz)

    date_now = datetime_now.date()
    time_now = datetime_now.replace(second=0, microsecond=0).time()
    now = datetime.combine(date_now, time_now)

    kickoff_time = match.time
    kickoff_date = match.date
    kickoff_datetime = datetime.combine(kickoff_date, kickoff_time)
    start_window = kickoff_datetime - timedelta(minutes=30)
    end_window = kickoff_datetime.replace(hour=23, minute=59, second=59)
    return start_window <= now <= end_window

@chat_bp.route('/chat', methods=["GET"])
@login_required
def chat():
    matches = FixtureFree.query.filter_by(round=find_current_round()).all()
    selected_match = matches[0] if matches else None

    chat_messages = []
    if selected_match:
        chat_messages = ChatMessage.query.filter_by(match_id=selected_match.match_id).order_by(ChatMessage.timestamp.asc()).all()

    return render_template(
        "chat.html",
        selected_match=selected_match,
        chat_messages=chat_messages,
        chat_open=True,
    )

@chat_bp.route('/chat/post_message', methods=["POST"])
@login_required
def post_message():
    match_id = request.form.get("match_id")
    message = request.form.get("message", "").strip()

    match = FixtureFree.query.filter(FixtureFree.match_id==match_id)
    #if not match or not is_chat_open(match):
    #    return jsonify({"error": "Chat is currently closed."}), 403
    print(f"HERE!!! MESSAGE: {message}")
    if message:
        new_msg = ChatMessage(
            user_id=current_user.id,
            match_id=match_id,
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
    match_id = request.args.get("match_id")
    match = FixtureFree.query.filter(FixtureFree.match_id==match_id)

    if not match:
        return jsonify({"error": "Invalid match."}), 400

    messages = ChatMessage.query.filter_by(match_id=match_id).order_by(ChatMessage.timestamp.asc()).all()
    
    result = [{
        "username": msg.user.username,
        "avatar": f"/static/avatars/{msg.user.avatar}",
        "message": msg.message,
        "timestamp": msg.timestamp.strftime("%H:%M")
    } for msg in messages]

    return jsonify({"messages": result})
