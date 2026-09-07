import os

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text

from config import Config
from db.db import db
from products.controllers.product_controller import product_controller


app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(product_controller)

CORS(
    app,
    supports_credentials=True,
    origins=[os.environ["FRONTEND_ORIGIN"]]
)


@app.route("/health", methods=["GET"])
def health():
    try:
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "status": "healthy",
            "service": "products"
        }), 200

    except Exception:
        return jsonify({
            "status": "unhealthy",
            "service": "products"
        }), 503
