"""Application Factory Flask."""
from pathlib import Path
from flask import Flask
from storage.models import db


def create_app(config_name: str = "development") -> Flask:
    """Crée et configure l'application Flask.

    Args:
        config_name: Nom de la configuration ('development', 'testing', etc.)

    Returns:
        Instance Flask configurée.
    """
    from app_factory.config import configs

    # Utiliser le répertoire racine du projet pour les templates/static
    root = Path(__file__).resolve().parent.parent

    app = Flask(
        __name__,
        template_folder=str(root / "templates"),
        static_folder=str(root / "static"),
        static_url_path="/static",
    )
    app.config.from_object(configs.get(config_name, configs["default"]))

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from app_factory.routes import main_bp
    app.register_blueprint(main_bp)

    return app
