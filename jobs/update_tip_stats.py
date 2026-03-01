import argparse

from app import create_app
from app.services.fixtures import upsert_free_fixtures, update_user_tip_stats


def parse_args():
    parser = argparse.ArgumentParser(
        description="Refresh fixtures and update user tip stats."
    )
    parser.add_argument(
        "--skip-fixtures",
        action="store_true",
        help="Skip refreshing fixture results before updating stats.",
    )
    return parser.parse_args()


def run(skip_fixtures: bool = False) -> None:
    app = create_app()
    with app.app_context():
        if not skip_fixtures:
            print("Refreshing fixtures...")
            upsert_free_fixtures()
        else:
            print("Skipping fixture refresh.")

        print("Updating user tip stats...")
        update_user_tip_stats()

        print("Done.")


if __name__ == "__main__":
    args = parse_args()
    run(skip_fixtures=args.skip_fixtures)
