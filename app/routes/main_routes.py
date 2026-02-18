# app/main_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, logout_user, current_user
from app.models import ChatMessage, FixtureFree
from app.services.fixtures import find_current_round
from app.utils.helper_functions import get_user_rank
from app.utils.team_logos import TEAM_LOGOS
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # if not current_user.is_authenticated:
    #     return redirect(url_for('auth.register'))
    round_number = find_current_round()
    fixtures = (
        FixtureFree.query.filter_by(round=round_number)
        .order_by(FixtureFree.date)
        .all()
        if round_number
        else []
    )
    rank = None
    if current_user.is_authenticated:
        rank = get_user_rank(current_user.username)
    chat_messages = []
    if round_number:
        chat_messages = (
            ChatMessage.query.filter_by(round_number=round_number)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )
    return render_template(
        'home.html',
        current_year=datetime.now().year,
        rank=rank,
        round_number=round_number,
        fixtures=fixtures,
        team_logos=TEAM_LOGOS,
        chat_messages=chat_messages,
        chat_open=bool(round_number),
    )

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))
