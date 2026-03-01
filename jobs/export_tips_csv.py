import argparse
import csv
from datetime import datetime
from pathlib import Path

from app import create_app
from app.models import Tip


def parse_args():
    parser = argparse.ArgumentParser(description="Export Tip rows to CSV.")
    parser.add_argument(
        "--output",
        help="Optional output filename (defaults to timestamped file).",
    )
    return parser.parse_args()


def run(output_name: str | None = None) -> Path:
    app = create_app()
    with app.app_context():
        tips = Tip.query.order_by(Tip.id).all()

        output_dir = Path(__file__).resolve().parent / "csv_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

        if output_name:
            filename = output_name
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tips_{timestamp}.csv"

        output_path = output_dir / filename

        with output_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(
                ["id", "match", "selected_team", "user_id", "username", "date"]
            )
            for tip in tips:
                writer.writerow(
                    [
                        tip.id,
                        tip.match,
                        tip.selected_team,
                        tip.user_id,
                        tip.username,
                        tip.date.isoformat() if tip.date else "",
                    ]
                )

    return output_path


if __name__ == "__main__":
    args = parse_args()
    output_path = run(output_name=args.output)
    print(f"Exported tips to {output_path}")
