import argparse

from app import create_app, db
from app.models import FixtureFree, Tip, User
from app.services.fixtures import find_current_round


def parse_args():
    parser = argparse.ArgumentParser(description="Auto-assign missing tips to away teams.")
    parser.add_argument(
        "--match-ids",
        help="Comma-separated match_ids to target (e.g., 1,2). Defaults to all in current round.",
    )
    return parser.parse_args()


def run(match_ids_override=None):
    app = create_app()
    with app.app_context():
        current_round = find_current_round()
        fixtures = FixtureFree.query.filter_by(round=current_round).all()

        if not fixtures:
            print("No fixtures found for current round.")
            return

        if match_ids_override:
            match_ids = [m.strip() for m in match_ids_override if m.strip()]
        else:
            match_ids = [str(f.match_id) for f in fixtures]
        tips = Tip.query.filter(Tip.match.in_(match_ids)).all()
        tips_by_user = {}
        for tip in tips:
            tips_by_user.setdefault(tip.user_id, set()).add(str(tip.match))

        target_fixtures = [f for f in fixtures if str(f.match_id) in match_ids]
        users = User.query.all()
        created = 0
        for user in users:
            existing = tips_by_user.get(user.id, set())
            missing_fixtures = [f for f in target_fixtures if str(f.match_id) not in existing]
            for fixture in missing_fixtures:
                new_tip = Tip(
                    user_id=user.id,
                    username=user.username,
                    match=str(fixture.match_id),
                    selected_team=fixture.away_team,
                )
                db.session.add(new_tip)
                created += 1

        if created:
            db.session.commit()
        print(f"Auto-assigned {created} missing tips for round {current_round}.")


if __name__ == "__main__":
    args = parse_args()
    match_ids = args.match_ids.split(",") if args.match_ids else None
    run(match_ids_override=match_ids)
