#Init File 

import os
from contextlib import contextmanager
from flask import Flask
from app.config import Config

@contextmanager
def get_db_connection():
    import psycopg
    from psycopg.rows import dict_row
    conn = psycopg.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "hardcount"),
        autocommit=True,
        row_factory=dict_row,
    )
    try:
        yield conn
    finally:
        conn.close()

def run_one(query, params=None, default=None):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchone()
    except Exception as exc:
        print(f"run_one error: {exc}")
        return default

def run_all(query, params=None, default=None):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
    except Exception as exc:
        print(f"run_all error: {exc}")
        return default if default is not None else []

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.routes.main import main_bp
    from app.routes.players import players_bp
    from app.routes.teams import teams_bp
    from app.routes.games import games_bp
    from app.routes.trades import trades_bp
    from app.routes.coaches import coaches_bp
    from app.routes.login import login_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(players_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(trades_bp)
    app.register_blueprint(coaches_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(admin_bp)

    return app
