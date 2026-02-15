# app/main_routes.py

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, logout_user, current_user
from app.models import Tip, FixtureFree, UserTipStats
from app.services.fixtures import find_current_round
from app.utils.team_logos import TEAM_LOGOS
from app.utils.helper_functions import get_user_rank
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # if not current_user.is_authenticated:
    #     return redirect(url_for('auth.register'))
    round_number = find_current_round()
    fixtures = FixtureFree.query.filter_by(round=round_number).order_by(FixtureFree.date).all()
    match_ids = [f.match_id for f in fixtures]
    rank = None
    tips = []
    if current_user.is_authenticated:
        rank = get_user_rank(current_user.username)
        tips = Tip.query.filter(Tip.user_id==current_user.id, Tip.match.in_(match_ids)).all()
    tip_map = {tip.match: tip.selected_team for tip in tips}
    result_map = {tip.match: FixtureFree.get_winning_team(tip.match) for tip in tips}
    print('HERE!!!', rank)
    return render_template('home.html', tips=tips, tip_map=tip_map, result_map=result_map, round_number=round_number, fixtures=fixtures, team_logos=TEAM_LOGOS, current_year=datetime.now().year, rank=rank)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))
