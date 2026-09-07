import os


class Config:
    DB_HOST = os.environ["USERS_DB_HOST"]
    DB_PORT = os.environ["USERS_DB_PORT"]
    DB_NAME = os.environ["USERS_DB_NAME"]
    DB_USER = os.environ["USERS_DB_USER"]
    DB_PASSWORD = os.environ["USERS_DB_PASSWORD"]

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True
    }
