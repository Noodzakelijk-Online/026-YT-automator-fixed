import logging
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
from errors import register_error_handlers
from extensions import db, migrate


def create_app(config_object=Config):
    load_dotenv(Path(__file__).with_name(".env"))
    app = Flask(__name__)
    app.config.from_object(config_object)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["GENERATED_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    from routes.auth import auth_bp
    from routes.core import api_bp
    from routes.playlists import playlists_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(playlists_bp, url_prefix="/api/playlists")
    register_error_handlers(app)

    @app.before_request
    def request_context():
        request.request_id = request.headers.get("X-Request-ID", str(uuid4()))

    @app.after_request
    def response_headers(response):
        response.headers["X-Request-ID"] = getattr(request, "request_id", "")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @app.cli.command("init-db")
    def init_db():
        """Create development tables; production should use flask db upgrade."""
        db.create_all()
        print("Database initialized")

    return app


app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")

