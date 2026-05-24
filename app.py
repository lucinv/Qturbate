"""Point d'entrée de l'application Flask."""
from app_factory import create_app

app = create_app("development")


def main():
    app.run(host='127.0.0.1', port=5001)


if __name__ == '__main__':
    main()
