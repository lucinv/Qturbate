"""Fixtures partagées pour les tests."""
from pathlib import Path
import sys

import pytest

from app_factory import create_app

# Ajouter la racine du projet au path pour les imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def app():
    """Fixture Flask app en mode test."""
    application = create_app("testing")
    return application


@pytest.fixture
def client(app):
    """Fixture client de test Flask."""
    return app.test_client()
