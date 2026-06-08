from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Tip, FixtureFree, User, UserTipStats
from app.utils.team_logos import TEAM_LOGOS
from datetime import date, timedelta
from sqlalchemy import func, asc
from sqlalchemy.orm import aliased
from sqlalchemy import over

leaderboard_bp = Blueprint('leaderboard', __name__)

@leaderboard_bp.route("/leaderboard", methods=["GET","POST"])
@login_required
def leaderboard():
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
    
    #building a subquery so i can use the windows function to calc running total
    subquery = (
        db.session.query(
            UserTipStats.round_number.label("round_number"),
            func.sum(UserTipStats.successful_tips + UserTipStats.bonus_tips).label("total_success"),
            func.sum(UserTipStats.pending_tips).label("total_pending")
        )
        .filter(UserTipStats.user_id == current_user.id)
        .group_by(UserTipStats.round_number)
        .subquery()
    )

    
    alias = aliased(subquery)

    
    round_data = (
        db.session.query(
            alias.c.round_number,
            alias.c.total_success,
            alias.c.total_pending,
            over(
                func.sum(alias.c.total_success),
                order_by=alias.c.round_number
            ).label("running_total_success")
        )
        .order_by(alias.c.round_number)
        .all()
    )
    

    return render_template("leaderboard.html", leaderboard_data=leaderboard_data, round_data=round_data)

