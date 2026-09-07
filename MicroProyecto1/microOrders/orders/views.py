import os

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text

from config import Config
from db.db import db
from orders.controllers.order_controller import order_controller


app = Flask(__name__)

app.config.from_object(Config)

# Misma clave que microUsers
app.config["SECRET_KEY"] = os.environ[
    "FLASK_SECRET_KEY"
]

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

db.init_app(app)

app.register_blueprint(
    order_controller
)

CORS(
    app,
    supports_credentials=True,
    origins=[
        os.environ["FRONTEND_ORIGIN"]
    ]
)


@app.route("/health", methods=["GET"])
def health():

    try:
        db.session.execute(
            text("SELECT 1")
        )

        return jsonify({
            "status": "healthy",
            "service": "orders"
        }), 200

    except Exception:

        return jsonify({
            "status": "unhealthy",
            "service": "orders"
        }), 503
