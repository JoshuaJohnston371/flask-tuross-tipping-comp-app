import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from app.models import Fixture, FixtureFree, db, User, UserTipStats, Tip
from app import create_app, db
from datetime import datetime, date, time, timedelta
import pytz
from app.services.fixtures import find_current_round
from sqlalchemy import func, over

SYDNEY_TZ = pytz.timezone("Australia/Sydney")

def get_user_rank(username):
    aggregated_data = (
        db.session.query(
            User.username,
            db.func.sum(UserTipStats.successful_tips + UserTipStats.bonus_tips).label("total_success"),
            db.func.sum(UserTipStats.pending_tips).label("total_pending")
        )
        .join(User, User.id == UserTipStats.user_id)
        .filter(~User.username.in_(['joshua_johnston','testing_db2']))
        .group_by(User.username)
        .subquery()
    )
    
    leaderboard_data = (
        db.session.query(
            aggregated_data.c.username,
            aggregated_data.c.total_success,
            aggregated_data.c.total_pending,
            over(
                func.dense_rank(),
                order_by=db.desc(aggregated_data.c.total_success)
            ).label("rank")
        )
        .order_by(db.asc("rank"))
        .all()
    )

    # Iterate through sorted leaderboard to find rank
    for idx, row in enumerate(leaderboard_data, start=1):
        if row.username == username:
            return row.rank  # Rank starts at 1

    return None

    

def has_user_submitted_tips(user_id):
    match_ids = [f.match_id for f in FixtureFree.query.filter_by(round=find_current_round()).all()]
    tips = Tip.query.filter(Tip.user_id==user_id, Tip.match.in_(match_ids)).all()
    
    if len(match_ids)==len(set(t.match for t in tips)):
        return True
    else:
        return False

def get_all_rounds():
    rounds = db.session.query(FixtureFree.round).distinct().order_by(FixtureFree.round).all()
    return [r[0] for r in rounds]


def get_round_tips_cutoff(round_number):
    """Return the Thursday 5pm Sydney deadline for a round based on its first fixture."""
    fixtures = (
        FixtureFree.query
        .filter(FixtureFree.round == round_number, FixtureFree.date.isnot(None))
        .order_by(FixtureFree.date.asc())
        .all()
    )
    if not fixtures:
        return None

    first_game_date = fixtures[0].date
    days_to_thursday = 3 - first_game_date.weekday()
    thursday_date = first_game_date + timedelta(days=days_to_thursday)
    return SYDNEY_TZ.localize(datetime.combine(thursday_date, time(17, 0, 0)))


def is_past_round_tips_cutoff(round_number):
    cutoff = get_round_tips_cutoff(round_number)
    if cutoff is None:
        return False
    return datetime.now(SYDNEY_TZ) >= cutoff


def is_past_thursday_5pm_aus():
    now = datetime.now(pytz.timezone('Australia/Sydney'))
    
    # Calculate the start of the week (Monday at 12:01 AM)
    monday = now - timedelta(days=now.weekday())  # Get the previous Monday
    monday = monday.replace(hour=0, minute=1, second=0, microsecond=0)

    # Calculate the end of the week (Sunday at 11:59 PM)
    sunday = monday + timedelta(days=6)  # Get the next Sunday
    sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)

    days_until_thursday = (3 - now.weekday()) % 7
    thursday = now - timedelta(days=now.weekday() - 3)
    thursday_5pm = thursday.replace(hour=17, minute=0, second=0, microsecond=0)


    if monday <= now <= thursday_5pm:
        return False
    elif thursday_5pm <= now <= sunday:
        return True 
    else:
        return False
