import unittest

from app import create_app, db


class GamesApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "ADMIN_API_TOKEN": "test-admin-token",
                "CORS_ORIGINS": "http://localhost:5173",
            }
        )
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.admin_headers = {"Authorization": "Bearer test-admin-token"}
        self.game = {
            "title": "Prueba",
            "description": "Juego para probar la API",
            "year": 2024,
            "genre": "Arcade",
            "era": "Siglo XXI",
            "image": "/prueba.jpg",
            "url": "https://example.com/prueba",
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_public_list_returns_empty_collection(self):
        response = self.client.get("/api/games")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"games": []})

    def test_write_requires_admin_token(self):
        response = self.client.post("/api/games", json=self.game)
        self.assertEqual(response.status_code, 401)

    def test_create_update_and_delete_game(self):
        created = self.client.post(
            "/api/games",
            json=self.game,
            headers=self.admin_headers,
        )
        self.assertEqual(created.status_code, 201)
        game = created.get_json()["game"]
        self.assertGreater(game["id"], 0)
        self.assertEqual(game["title"], "Prueba")

        listed = self.client.get("/api/games")
        self.assertEqual(listed.get_json()["games"], [game])

        detail = self.client.get(f"/api/games/{game['id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["game"], game)

        updated = self.client.patch(
            f"/api/games/{game['id']}",
            json={"title": "Prueba editada"},
            headers=self.admin_headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["game"]["title"], "Prueba editada")
        self.assertEqual(updated.get_json()["game"]["year"], 2024)

        replacement = {
            **self.game,
            "title": "Reemplazo completo",
        }
        replaced = self.client.put(
            f"/api/games/{game['id']}",
            json=replacement,
            headers=self.admin_headers,
        )
        self.assertEqual(replaced.status_code, 200)
        self.assertEqual(replaced.get_json()["game"]["title"], "Reemplazo completo")

        deleted = self.client.delete(
            f"/api/games/{game['id']}",
            headers=self.admin_headers,
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get("/api/games").get_json()["games"], [])

    def test_invalid_game_payload_is_rejected(self):
        invalid_game = {**self.game, "year": True}
        response = self.client.post(
            "/api/games",
            json=invalid_game,
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("year", response.get_json()["error"])

    def test_missing_game_returns_not_found(self):
        response = self.client.get("/api/games/999")
        self.assertEqual(response.status_code, 404)

    def test_cors_allows_configured_frontend_origin(self):
        response = self.client.options(
            "/api/games",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://localhost:5173")
        self.assertIn("Authorization", response.headers["Access-Control-Allow-Headers"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
