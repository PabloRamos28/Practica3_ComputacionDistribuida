import hmac
import os
from functools import wraps

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()

db = SQLAlchemy()

GAME_FIELDS = ("title", "description", "year", "genre", "era", "image", "url")
STRING_FIELDS = ("title", "description", "genre", "era", "image", "url")


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    era = db.Column(db.String(40), nullable=False)
    image = db.Column(db.String(2048), nullable=False, default="")
    url = db.Column(db.String(2048), nullable=False, default="")

    def to_dict(self):
        return {field: getattr(self, field) for field in ("id", *GAME_FIELDS)}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://localhost:5432/arcade",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ADMIN_API_TOKEN=os.environ.get("ADMIN_API_TOKEN", ""),
        CORS_ORIGINS=os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"),
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)

    allowed_origins = {
        origin.strip()
        for origin in app.config["CORS_ORIGINS"].split(",")
        if origin.strip()
    }

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    def admin_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            expected_token = app.config["ADMIN_API_TOKEN"]
            if not expected_token:
                return jsonify(error="El backend no tiene configurado ADMIN_API_TOKEN."), 503

            auth_header = request.headers.get("Authorization", "")
            scheme, _, supplied_token = auth_header.partition(" ")
            if (
                scheme.lower() != "bearer"
                or not supplied_token
                or not hmac.compare_digest(supplied_token, expected_token)
            ):
                return jsonify(error="Se requiere un token de administrador válido."), 401
            return view(*args, **kwargs)

        return wrapped

    def read_game_payload(existing_game=None):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return None, (jsonify(error="El cuerpo de la petición debe ser un objeto JSON."), 400)

        unknown_fields = set(payload) - set(GAME_FIELDS)
        if unknown_fields:
            return None, (
                jsonify(error=f"Campos no permitidos: {', '.join(sorted(unknown_fields))}."),
                400,
            )

        values = existing_game.to_dict() if existing_game else {}
        values.pop("id", None)
        values.update(payload)
        missing_fields = [field for field in GAME_FIELDS if field not in values]
        if missing_fields:
            return None, (
                jsonify(error=f"Faltan campos obligatorios: {', '.join(missing_fields)}."),
                400,
            )

        for field in STRING_FIELDS:
            value = values[field]
            if not isinstance(value, str) or not value.strip():
                return None, (jsonify(error=f"'{field}' debe ser un texto no vacío."), 400)
            values[field] = value.strip()

        year = values["year"]
        if isinstance(year, bool) or not isinstance(year, int) or year < 1 or year > 9999:
            return None, (jsonify(error="'year' debe ser un año entero entre 1 y 9999."), 400)

        return values, None

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    @app.get("/api/games")
    def list_games():
        games = db.session.scalars(select(Game).order_by(Game.title, Game.id)).all()
        return jsonify(games=[game.to_dict() for game in games])

    @app.get("/api/games/<int:game_id>")
    def get_game(game_id):
        game = db.session.get(Game, game_id)
        if game is None:
            return jsonify(error="No se encontró el juego."), 404
        return jsonify(game=game.to_dict())

    @app.post("/api/games")
    @admin_required
    def create_game():
        values, error = read_game_payload()
        if error:
            return error

        game = Game(**values)
        db.session.add(game)
        db.session.commit()
        return jsonify(game=game.to_dict()), 201

    @app.route("/api/games/<int:game_id>", methods=["PUT", "PATCH"])
    @admin_required
    def update_game(game_id):
        game = db.session.get(Game, game_id)
        if game is None:
            return jsonify(error="No se encontró el juego."), 404

        values, error = read_game_payload(game if request.method == "PATCH" else None)
        if error:
            return error

        for field, value in values.items():
            setattr(game, field, value)
        db.session.commit()
        return jsonify(game=game.to_dict())

    @app.delete("/api/games/<int:game_id>")
    @admin_required
    def delete_game(game_id):
        game = db.session.get(Game, game_id)
        if game is None:
            return jsonify(error="No se encontró el juego."), 404

        db.session.delete(game)
        db.session.commit()
        return "", 204

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Tablas de la API creadas.")

    return app


app = create_app()
