import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import _database_url, create_app, db


class GamesApiTestCase(unittest.TestCase):
    def test_postgresql_url_selects_installed_psycopg2_driver(self):
        with patch.dict(
            "os.environ",
            {"DATABASE_URL": "postgresql://postgres:secret@localhost:5432/games_db"},
        ):
            self.assertEqual(
                _database_url(),
                "postgresql+psycopg2://postgres:secret@localhost:5432/games_db",
            )

        with patch.dict(
            "os.environ",
            {"DATABASE_URL": "postgres://postgres:secret@localhost:5432/games_db"},
        ):
            self.assertEqual(
                _database_url(),
                "postgresql+psycopg2://postgres:secret@localhost:5432/games_db",
            )

    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "JWT_SECRET_KEY": "test-secret-key-with-at-least-32-bytes",
                "API_USERNAME": "test-admin",
                "API_PASSWORD": "test-password",
                "CORS_ORIGINS": [],
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def authenticate(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "test-admin", "password": "test-password"},
        )
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json['access_token']}"}

    def test_list_games_is_public_and_returns_created_games(self):
        self.assertEqual(self.client.get("/api/games").status_code, 200)
        headers = self.authenticate()
        created = self.client.post(
            "/api/games",
            headers=headers,
            json={"title": "Portal 2", "genre": "Puzzle", "platform": "PC"},
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json["release_year"], None)
        self.assertEqual(
            self.client.get("/api/games").json,
            [created.json],
        )

    def test_create_edit_and_delete_game_requires_authentication(self):
        game_data = {
            "title": "Hades",
            "genre": "Roguelike",
            "platform": "PC",
            "release_year": 2020,
            "description": "An action game",
        }
        self.assertEqual(
            self.client.post("/api/games", json=game_data).status_code, 401
        )

        headers = self.authenticate()
        created = self.client.post("/api/games", headers=headers, json=game_data)
        self.assertEqual(created.status_code, 201)
        game_id = created.json["id"]

        patched = self.client.patch(
            f"/api/games/{game_id}",
            headers=headers,
            json={"platform": "Nintendo Switch"},
        )
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.json["title"], "Hades")
        self.assertEqual(patched.json["platform"], "Nintendo Switch")

        replaced = self.client.put(
            f"/api/games/{game_id}",
            headers=headers,
            json={"title": "Hades II", "genre": "Action", "platform": "PC"},
        )
        self.assertEqual(replaced.status_code, 200)
        self.assertIsNone(replaced.json["release_year"])
        self.assertEqual(replaced.json["description"], "")

        self.assertEqual(
            self.client.delete(f"/api/games/{game_id}", headers=headers).status_code,
            204,
        )
        self.assertEqual(self.client.get(f"/api/games/{game_id}").status_code, 404)

    def test_rejects_invalid_payloads_and_credentials(self):
        bad_login = self.client.post(
            "/api/auth/login",
            json={"username": "test-admin", "password": "wrong"},
        )
        self.assertEqual(bad_login.status_code, 401)

        headers = self.authenticate()
        missing_required = self.client.post(
            "/api/games", headers=headers, json={"title": "Incomplete"}
        )
        self.assertEqual(missing_required.status_code, 400)
        invalid_year = self.client.post(
            "/api/games",
            headers=headers,
            json={
                "title": "Invalid",
                "genre": "Test",
                "platform": "PC",
                "release_year": True,
            },
        )
        self.assertEqual(invalid_year.status_code, 400)
        unknown_field = self.client.post(
            "/api/games",
            headers=headers,
            json={
                "title": "Unknown",
                "genre": "Test",
                "platform": "PC",
                "owner": "somebody",
            },
        )
        self.assertEqual(unknown_field.status_code, 400)


if __name__ == "__main__":
    unittest.main()
