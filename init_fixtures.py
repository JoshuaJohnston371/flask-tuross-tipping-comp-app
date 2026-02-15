# init_fixtures.py

from app import create_app, db
from app.services.fixtures import upsert_free_fixtures

app = create_app()

with app.app_context():
    season = 2026
    max_round = 27  # Adjust if 2026 has more or fewer rounds

    upsert_free_fixtures()
    
    '''for round_ in range(1, 2):
        print(f"Processing season {season}, round {round_}")
        upsert_fixtures(season, round_)
     '''   
    
    print("Fixture initialization complete.")
