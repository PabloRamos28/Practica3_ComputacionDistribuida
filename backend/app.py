import hmac
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_sqlalchemy import SQLAlchemy


load_dotenv(Path(__file__).with_name(".env"), override=False)

db = SQLAlchemy()
jwt = JWTManager()

REQUIRED_GAME_FIELDS = ("title", "genre", "platform")
GAME_FIELDS = set(REQUIRED_GAME_FIELDS) | {"release_year", "description"}
STRING_LIMITS = {"title": 200, "genre": 100, "platform": 100, "description": 2000}


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    platform = db.Column(db.String(100), nullable=False)
    release_year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=False, default="")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "genre": self.genre,
            "platform": self.platform,
            "release_year": self.release_year,
            "description": self.description,
        }


def _json_error(message, status):
    return jsonify({"error": message}), status


def _database_url():
    url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/games_db"
    )
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


def _game_payload(partial=False):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    unknown_fields = set(payload) - GAME_FIELDS
    if unknown_fields:
        return None, f"Unknown field(s): {', '.join(sorted(unknown_fields))}."

    if not partial:
        missing_fields = set(REQUIRED_GAME_FIELDS) - set(payload)
        if missing_fields:
            return None, f"Missing required field(s): {', '.join(sorted(missing_fields))}."
    elif not payload:
        return None, "At least one game field must be provided."

    cleaned = {}
    for field, limit in STRING_LIMITS.items():
        if field not in payload:
            continue
        value = payload[field]
        if not isinstance(value, str):
            return None, f"'{field}' must be a string."
        value = value.strip()
        if field != "description" and not value:
            return None, f"'{field}' cannot be empty."
        if len(value) > limit:
            return None, f"'{field}' must be at most {limit} characters."
        cleaned[field] = value

    if "release_year" in payload:
        year = payload["release_year"]
        if year is not None and (
            isinstance(year, bool) or not isinstance(year, int) or not 1 <= year <= 9999
        ):
            return None, "'release_year' must be an integer between 1 and 9999, or null."
        cleaned["release_year"] = year

    return cleaned, None


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=_database_url(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1),
        API_USERNAME=os.getenv("API_USERNAME"),
        API_PASSWORD=os.getenv("API_PASSWORD"),
        CORS_ORIGINS=os.getenv(
            "CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
        ),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)
    origins = app.config["CORS_ORIGINS"]
    if isinstance(origins, str):
        origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins}})

    @jwt.unauthorized_loader
    def missing_token(_reason):
        return _json_error("A valid access token is required.", 401)

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return _json_error("The access token is invalid.", 401)

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return _json_error("The access token has expired.", 401)

    @app.errorhandler(404)
    def not_found(_error):
        return _json_error("Resource not found.", 404)

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return _json_error("Method not allowed.", 405)

    @app.post("/api/auth/login")
    def login():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return _json_error("Request body must be a JSON object.", 400)

        username = app.config["API_USERNAME"]
        password = app.config["API_PASSWORD"]
        jwt_secret = app.config["JWT_SECRET_KEY"]
        if not username or not password or not jwt_secret:
            app.logger.error("API_USERNAME, API_PASSWORD, and JWT_SECRET_KEY must be configured.")
            return _json_error("Authentication is not configured on the server.", 503)

        supplied_username = payload.get("username")
        supplied_password = payload.get("password")
        if not isinstance(supplied_username, str) or not isinstance(supplied_password, str):
            return _json_error("Username and password are required.", 400)
        if not hmac.compare_digest(
            supplied_username.encode("utf-8"), username.encode("utf-8")
        ) or not hmac.compare_digest(
            supplied_password.encode("utf-8"), password.encode("utf-8")
        ):
            return _json_error("Invalid username or password.", 401)

        token = create_access_token(identity=username)
        return jsonify({"access_token": token, "token_type": "Bearer"}), 200

    @app.get("/api/games")
    def list_games():
        games = db.session.execute(db.select(Game).order_by(Game.id)).scalars().all()
        return jsonify([game.to_dict() for game in games])

    @app.get("/api/games/<int:game_id>")
    def get_game(game_id):
        game = db.session.get(Game, game_id)
        if game is None:
            return _json_error("Game not found.", 404)
        return jsonify(game.to_dict())

    @app.post("/api/games")
    @jwt_required()
    def create_game():
        payload, error = _game_payload()
        if error:
            return _json_error(error, 400)
        payload.setdefault("release_year", None)
        payload.setdefault("description", "")

        game = Game(**payload)
        db.session.add(game)
        db.session.commit()
        return jsonify(game.to_dict()), 201, {
            "Location": url_for("get_game", game_id=game.id)
        }

    @app.put("/api/games/<int:game_id>")
    @jwt_required()
    def replace_game(game_id):
        game = db.session.get(Game, game_id)
        if game is None:
            return _json_error("Game not found.", 404)
        payload, error = _game_payload()
        if error:
            return _json_error(error, 400)
        payload.setdefault("release_year", None)
        payload.setdefault("description", "")
        for field, value in payload.items():
            setattr(game, field, value)
        db.session.commit()
        return jsonify(game.to_dict())

    @app.patch("/api/games/<int:game_id>")
    @jwt_required()
    def update_game(game_id):
        game = db.session.get(Game, game_id)
        if game is None:
            return _json_error("Game not found.", 404)
        payload, error = _game_payload(partial=True)
        if error:
            return _json_error(error, 400)
        for field, value in payload.items():
            setattr(game, field, value)
        db.session.commit()
        return jsonify(game.to_dict())

    @app.delete("/api/games/<int:game_id>")
    @jwt_required()
    def delete_game(game_id):
        game = db.session.get(Game, game_id)
        if game is None:
            return _json_error("Game not found.", 404)
        db.session.delete(game)
        db.session.commit()
        return "", 204

    @app.cli.command("init-db")
    def init_db():
        """Create the database tables."""
        db.create_all()
        print("Database tables created.")

    return app


app = create_app()
