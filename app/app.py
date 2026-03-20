import os
from contextlib import contextmanager

from flask import Flask, render_template
import psycopg
from psycopg.rows import dict_row


def create_app() -> Flask:
    app = Flask(__name__)

    @contextmanager
    def get_db_connection():
        conn = psycopg.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", os.getenv("USER", "postgres")),
            password=os.getenv("DB_PASSWORD", ""),
            dbname=os.getenv("DB_NAME", "hardcount"),
            autocommit=True,
            row_factory=dict_row,
        )
        try:
            yield conn
        finally:
            conn.close()

    def run_one(query: str, default=None):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    return cur.fetchone()
        except Exception as exc:
            app.logger.exception("Query failed in run_one: %s", exc)
            return default

    def run_all(query: str, default=None):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    return cur.fetchall()
        except Exception as exc:
            app.logger.exception("Query failed in run_all: %s", exc)
            return default if default is not None else []

    @app.route("/")
    def index():
        stats = run_one(
            """
            SELECT
                (SELECT COUNT(*) FROM team) AS teams,
                (SELECT COUNT(*) FROM player) AS players,
                (SELECT COUNT(*) FROM season_stats) AS season_rows
            """,
            default={"teams": 0, "players": 0, "season_rows": 0},
        )
        db_ok = stats is not None and not (
            stats.get("teams", 0) == 0
            and stats.get("players", 0) == 0
            and stats.get("season_rows", 0) == 0
        )
        if stats is None:
            stats = {"teams": 0, "players": 0, "season_rows": 0}
        return render_template("index.html", stats=stats, db_ok=db_ok)

    @app.route("/teams")
    def teams():
        rows = run_all(
            """
            SELECT
                t.name,
                COUNT(pf.player_name) AS roster_entries
            FROM team t
            LEFT JOIN playsfor pf ON pf.team_id = t.team_id
            GROUP BY t.name
            ORDER BY t.name
            """
        )
        return render_template("teams.html", teams=rows)

    @app.route("/players")
    def players():
        rows = run_all(
            """
            SELECT
                s.player_name,
                s.player_number,
                s.season,
                COALESCE(t.name, 'Unknown') AS team_name,
                s.season_rushing_yards,
                s.season_passing_yards,
                s.season_receiving_yards
            FROM season_stats s
            LEFT JOIN playsfor pf
                ON pf.player_name = s.player_name
               AND pf.player_number = s.player_number
               AND pf.season = s.season
            LEFT JOIN team t
                ON t.team_id = pf.team_id
            ORDER BY s.season_rushing_yards DESC
            LIMIT 25
            """
        )
        return render_template("players.html", players=rows)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
