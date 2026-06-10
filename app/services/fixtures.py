import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from app.models import Fixture, FixtureFree, db, User, UserTipStats, Tip
from app import create_app 
from datetime import datetime, date, timedelta
import pytz

# Load environment variables
load_dotenv()

#Functions for Free API
def get_free_nrl_fixtures():
    url = "https://fixturedownload.com/feed/json/nrl-2026"
    response = requests.get(url)
    if response.status_code == 200:
        fixtures = response.json()
        if isinstance(fixtures, list) and isinstance(fixtures[0], dict):
            return fixtures
        else:
            print(f"Unexpected fixture format:", fixtures)
            return []
    else:
        print("Failed to fetch fixtures:", response.status_code)
        return []
        
def upsert_free_fixtures():
    #FixtureFree.query.delete()
    #db.session.commit()
    
    fixtures = get_free_nrl_fixtures()
    
    if not fixtures:
        print("No fixtures fetched. Abort...")
        return 
    
    existing_fixtures = {
        f.match_id: f for f in FixtureFree.query.all()
    }
    
    for fixture in fixtures:
        #Converting fixtures date string to datetime format
        match_id = fixture.get("MatchNumber")
        round = fixture.get("RoundNumber")
        home_team = fixture.get("HomeTeam")
        away_team = fixture.get("AwayTeam")
        home_score = fixture.get("HomeTeamScore")
        away_score = fixture.get("AwayTeamScore")
        
        date_str = fixture.get("DateUtc", None)
        if date_str:
            try:
                # Replace 'Z' with '+00:00' to make it ISO-compliant
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

                # Already timezone-aware in UTC, so we can convert directly
                sydney_zone = pytz.timezone("Australia/Sydney")
                sydney_time = date_obj.astimezone(sydney_zone)

                # Split into date and time
                date_part = sydney_time.date()
                time_part = sydney_time.replace(second=0, microsecond=0).time()

            except ValueError:
                date_part = None
                time_part = None
        else:
            date_part = None
            time_part = None
        
        existing = existing_fixtures.get(str(match_id))

        if existing:
            updated = False
            if existing.home_score is None and home_score is not None:
                existing.home_score = home_score
                updated = True
            if existing.away_score is None and away_score is not None:
                existing.away_score = away_score
                updated = True
            if updated==True:
                print(f"updated scores for match: {match_id}")
        else:
        
            new_fixture = FixtureFree(
                match_id=fixture.get("MatchNumber", None),
                season=2026,
                round=fixture.get("RoundNumber",None),
                home_team=fixture.get("HomeTeam",None),
                away_team=fixture.get("AwayTeam", None),
                home_score=fixture.get("HomeTeamScore", None),
                away_score=fixture.get("AwayTeamScore", None),
                date=date_part,
                time=time_part
            )
            db.session.add(new_fixture)
            print(f"Inserted new fixture {match_id}")
            

    db.session.commit()


def find_current_round() -> int:
    sydney_tz = pytz.timezone("Australia/Sydney")
    today = datetime.now(sydney_tz).date()

    round1_start = date(2026, 3, 1)
    round1_end = date(2026, 3, 8)
    if today < round1_start:
        return 1
    if round1_start <= today <= round1_end:
        return 1

    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    # Use the highest round in the calendar week so a new round starts on Monday
    # even when the previous round has a long-weekend Monday game (e.g. round 14).
    current_round = (FixtureFree.query
                     .with_entities(FixtureFree.round)
                     .filter(FixtureFree.date >= monday, FixtureFree.date <= sunday)
                     .distinct()
                     .order_by(FixtureFree.round.desc())
                     .first()
                     )
    if current_round:
        return current_round[0]
    else:
        print("Current round returned empty")
        return 0

#Helper function to evaluate user round results
def get_user_round_results(user_id, round_number):
    fixtures = FixtureFree.query.filter_by(round=round_number).all()
    match_ids = [f.match_id for f in fixtures]
    tips = Tip.query.filter(Tip.user_id==user_id, Tip.match.in_(match_ids)).all()
    
    tip_map = {tip.match: tip.selected_team for tip in tips}
    results_map = {tip.match: FixtureFree.get_winning_team(tip.match) for tip in tips}
    
    round_results = {
        "success" : 0,
        "failure" : 0,
        "pending" : 0
    }
    
    for match_id, team in results_map.items():
        if team == None:
            round_results['pending'] += 1
        elif team == tip_map.get(match_id):
            round_results['success'] += 1
        else:
            round_results["failure"] += 1
            
    return round_results

def is_perfect_round(user_id, round_number, round_results):
    fixtures = FixtureFree.query.filter_by(round=round_number).all()
    match_ids = [f.match_id for f in fixtures]
    tips = Tip.query.filter(Tip.user_id == user_id, Tip.match.in_(match_ids)).all()

    if len(tips) != len(match_ids):
        return False

    return (
        round_results["success"] > 0
        and round_results["failure"] == 0
        and round_results["pending"] == 0
    )

# --- New Function to Update UserTipStats ---
def update_user_tip_stats():
    users = User.query.all()

    for user in users:
        for round_number in range(1, find_current_round() + 1): 
            round_results = get_user_round_results(user.id, round_number)
            bonus_tips = 1 if is_perfect_round(user.id, round_number, round_results) else 0

            stat = UserTipStats.query.filter_by(user_id=user.id, round_number=round_number).first()
            if stat:
                stat.successful_tips = round_results["success"]
                stat.failed_tips = round_results["failure"]
                stat.pending_tips = round_results["pending"]
                stat.bonus_tips = bonus_tips
            else:
                stat = UserTipStats(
                    user_id=user.id,
                    round_number=round_number,
                    successful_tips=round_results["success"],
                    failed_tips=round_results["failure"],
                    pending_tips=round_results["pending"],
                    bonus_tips=bonus_tips
                )
                db.session.add(stat)
    db.session.commit()
    
def main():
    app = create_app()
    with app.app_context():
        print("Refreshing fixtures...")
        upsert_free_fixtures()

        print("Updating user tip stats...")
        update_user_tip_stats()

        print("Done.")