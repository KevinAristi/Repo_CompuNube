import os

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text

from users.controllers.user_controller import user_controller
from db.db import db


app = Flask(__name__)

# Configuracion de base de datos
app.config.from_object("config.Config")

# La misma clave sera compartida posteriormente con microOrders
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]

# Configuracion de cookie de sesion para el laboratorio
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

db.init_app(app)

# Registrar endpoints de usuarios
app.register_blueprint(user_controller)

# Permitir al frontend enviar/recibir la cookie de sesion
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
            "service": "users"
        }), 200
    except Exception:
        return jsonify({
            "status": "unhealthy",
            "service": "users"
        }), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
