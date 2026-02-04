from app import create_app
from app.extensions import db
from config import Config

app = create_app(Config)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(
        # host="0.0.0.0",
        port=5001,
        debug=app.config.get("DEBUG_MODE"),
        threaded=True,
    )
