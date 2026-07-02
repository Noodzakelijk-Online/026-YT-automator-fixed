import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import create_app
from extensions import db


@pytest.fixture()
def app(tmp_path):
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test"
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        MAX_CONTENT_LENGTH = 1024 * 1024
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        GENERATED_FOLDER = str(tmp_path / "generated")
        GOOGLE_CLIENT_SECRETS_FILE = ""
        OPENAI_API_KEY = ""
        OPENAI_MODEL = "gpt-4o-mini"
        FRONTEND_URL = "http://localhost"
        CORS_ORIGINS = ["http://localhost"]
        TOKEN_ENCRYPTION_KEY = ""
        WORKER_POLL_SECONDS = 1
        JOB_MAX_RETRIES = 3
    value = create_app(TestConfig)
    with value.app_context():
        db.create_all()
        yield value
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
