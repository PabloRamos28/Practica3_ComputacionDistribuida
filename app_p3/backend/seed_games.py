import json
from pathlib import Path

from backend.app import create_app, db, Game


def main():
    app = create_app()
    games_path = Path(__file__).resolve().parents[1] / "games.json"
    with games_path.open(encoding="utf-8") as games_file:
        games = json.load(games_file)

    with app.app_context():
        if db.session.query(Game.id).first() is not None:
            raise SystemExit("La tabla ya contiene juegos; no se importó el catálogo inicial.")
        db.session.add_all(Game(**game) for game in games)
        db.session.commit()
        print(f"Se importaron {len(games)} juegos.")


if __name__ == "__main__":
    main()
