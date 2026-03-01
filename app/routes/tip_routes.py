from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Tip, FixtureFree, User
from app.utils.team_logos import TEAM_LOGOS
from datetime import date, datetime, timedelta
from app.utils.helper_functions import get_all_rounds, is_past_thursday_5pm_aus
from app.services.fixtures import find_current_round
from app.services.analyst_agent import generate_match_report
import pytz

tip_bp = Blueprint('tip', __name__)
REPORT_CACHE = {}

@tip_bp.route('/submit_tip', methods=['GET', 'POST'])
@login_required
def submit_tip():
    sydney_tz = pytz.timezone("Australia/Sydney")
    now = datetime.now(sydney_tz)
    current_round = find_current_round()

    fixtures = FixtureFree.query.filter(FixtureFree.round == current_round).all()
    
    match_ids = [str(f.match_id) for f in fixtures]
    
    existing_tips = Tip.query.filter(Tip.user_id == current_user.id, Tip.match.in_(match_ids)).all()
    existing_match_ids = {str(t.match) for t in existing_tips}
    has_submitted = set(match_ids).issubset(existing_match_ids)

    required_match_ids = set(match_ids)
    tips_closed = False
    if current_round == 1:
        round1_first_cutoff = sydney_tz.localize(datetime(2026, 2, 28, 17, 0, 0))
        round1_cutoff = sydney_tz.localize(datetime(2026, 3, 5, 17, 0, 0))
        if now >= round1_cutoff:
            tips_closed = True
        elif now < round1_first_cutoff:
            required_match_ids = {m for m in match_ids if m in {"1", "2"}}
        else:
            required_match_ids = {m for m in match_ids if m not in {"1", "2"}}

    visible_fixtures = [f for f in fixtures if str(f.match_id) in required_match_ids]
    
    if request.method == 'POST':
        if tips_closed:
            flash('Tip submissions for round 1 are now closed.', 'danger')
            return redirect(url_for('main.home'))
        if has_submitted:
            flash('You have already submitted your tips.', 'warning')
            return redirect(url_for('main.home'))

        for fixture in visible_fixtures:
            match_id = str(fixture.match_id)
            if match_id in existing_match_ids:
                continue
            selected_team = request.form.get(f'team-input-{match_id}')

            if not selected_team:
                flash('You must select a team for all matches.', 'danger')
                return redirect(url_for('tip.submit_tip'))

            new_tip = Tip(
                user_id=current_user.id,
                username=current_user.username,
                match=match_id,
                selected_team=selected_team
            )
            db.session.add(new_tip)

        db.session.commit()
        flash('Tips submitted successfully!', 'success')
        return redirect(url_for('main.home'))

    submitted_tips = []
    if has_submitted:
        match_lookup = {f.id: f for f in fixtures}
        for tip in existing_tips:
            fixture = match_lookup.get(tip.match)
            print("here!!!")
            print(match_lookup.get(73))
            submitted_tips.append({
                'selected_team': tip.selected_team,
                #'date': "TBD" fixture.date if fixture else None
            })

    return render_template(
        'submit_tip.html',
        fixtures=visible_fixtures,
        has_submitted=has_submitted,
        submitted_tips=submitted_tips,
        team_logos=TEAM_LOGOS
    )

@tip_bp.route("/view-tips")
@login_required
def view_tips():
    selected_round = request.args.get("round", type=int)
    all_rounds = get_all_rounds()
    sydney_tz = pytz.timezone("Australia/Sydney")
    now = datetime.now(sydney_tz)
    after_5_thursday = is_past_thursday_5pm_aus()

    if not selected_round:
        selected_round = find_current_round()

    fixtures = FixtureFree.query.filter_by(round=selected_round).order_by(FixtureFree.match_id.asc()).all()
    match_ids = [f.match_id for f in fixtures]

    users = User.query.filter(~User.username.in_(['testing_db2'])).all()
    tips_by_user = {
        user.id: Tip.query.filter(Tip.user_id == user.id, Tip.match.in_(match_ids)).all()
        for user in users if user.username not in ['testing_db2']
    }
    visibility_message = None
    visible_match_ids = match_ids

    #round 1 edge case 2026
    if selected_round == 1:
        round1_first_cutoff = sydney_tz.localize(datetime(2026, 2, 28, 17, 0, 0))
        round1_cutoff = sydney_tz.localize(datetime(2026, 3, 5, 17, 0, 0))
        if now < round1_first_cutoff:
            visible_match_ids = []
            visibility_message = "View others tips after 5pm Sat 28 Feb."
        elif now < round1_cutoff:
            visible_match_ids = [m for m in match_ids if m in ["1", "2", 1, 2]]
            visibility_message = "Only matches 1-2 visible until 5pm Thu 5 Mar."
        else:
            visible_match_ids = match_ids
    elif selected_round == find_current_round() and not after_5_thursday:
        visible_match_ids = []
        visibility_message = "View others tips after 5pm Thursday."

    visible_fixtures = [f for f in fixtures if f.match_id in visible_match_ids]
    results_map = {match: FixtureFree.get_winning_team(match) for match in visible_match_ids}

    display_tips_by_user = {}
    for user in users:
        user_tips = tips_by_user.get(user.id, [])
        if user.id != current_user.id:
            if visible_match_ids:
                user_tips = [t for t in user_tips if t.match in visible_match_ids]
            else:
                user_tips = []
        display_tips_by_user[user.id] = user_tips
    
    return render_template(
        "view_tips.html",
        users=users,
        tips_by_user=display_tips_by_user,
        selected_round=selected_round,
        all_rounds=all_rounds,
        fixtures=visible_fixtures,
        results_map=results_map,
        after_5_thursday=after_5_thursday, #dictate if user can see others tips
        current_round=find_current_round(),
        visibility_message=visibility_message
    )

@tip_bp.route("/tip-report/<match_id>")
@login_required
def tip_report(match_id):
    match_id = str(match_id)
    if match_id in REPORT_CACHE:
        return jsonify({"report": REPORT_CACHE[match_id], "cached": True})

    try:
        report = generate_match_report(match_id)
    except Exception as exc:
        return jsonify({"error": f"Report generation failed: {exc}"}), 503
    if not report:
        return jsonify({"error": "Reports are unavailable right now."}), 503

    REPORT_CACHE[match_id] = report
    return jsonify({"report": report, "cached": False})