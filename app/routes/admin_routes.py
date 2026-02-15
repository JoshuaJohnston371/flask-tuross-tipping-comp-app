from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app.models import User, Tip, FixtureFree
from datetime import date
from app import db
from app.services.fixtures import find_current_round
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for("main.index"))

    current_round = find_current_round()

    users = User.query.all()
    if current_round:
        current_fixtures = FixtureFree.query.filter_by(round=current_round).all()
        current_match_ids = [f.match_id for f in current_fixtures]
    else:
        current_fixtures = []
        current_match_ids = []
    avatar_folder = os.path.join(current_app.static_folder, "avatars")
    avatars = sorted([f for f in os.listdir(avatar_folder) if f.endswith((".png", ".jpg", ".jpeg"))])

    tips_by_user = {}
    for user in users:
        if current_match_ids:
            tips = Tip.query.filter(Tip.user_id == user.id, Tip.match.in_(current_match_ids)).all()
        else:
            tips = []
        tips_by_user[user.id] = tips

    # Handle Change Username form submission
    username_update_success = False
    username_update_error = None
    register_success = False
    register_error = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "change_username":
            user_id = request.form["user_id"]
            new_username = request.form["new_username"].strip()

            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                username_update_error = "Username already taken."
            else:
                user = User.query.get(user_id)
                if user:
                    user.username = new_username
                    db.session.commit()
                    username_update_success = True
                else:
                    username_update_error = "User not found."
        elif action == "register_user":
            name = request.form.get("name", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            phone_number = request.form.get("phone_number", "").strip()
            avatar = request.form.get("avatar", "").strip()

            if not username or not password:
                register_error = "Username and password are required."
            elif User.query.filter_by(username=username).first():
                register_error = "Username already exists."
            elif avatar and avatar not in avatars:
                register_error = "Invalid avatar selection."
            else:
                new_user = User(
                    name=name or None,
                    username=username,
                    phone_number=phone_number or None,
                    avatar=secure_filename(avatar) if avatar else "default.jpg",
                )
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                register_success = True

    return render_template(
        "admin.html",
        users=users,
        tips_by_user=tips_by_user,
        round=current_round,
        username_update_success=username_update_success,
        username_update_error=username_update_error,
        register_success=register_success,
        register_error=register_error,
        avatars=avatars,
    )
