import os
from contextlib import contextmanager

from flask import Flask, render_template, request
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

    def run_one(query: str, params=None, default=None):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params or ())
                    return cur.fetchone()
        except Exception as exc:
            app.logger.exception("Query failed in run_one: %s", exc)
            return default

    def run_all(query: str, params=None, default=None):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params or ())
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
        sort = request.args.get("sort", "rushing")
        order = request.args.get("order", "desc")

        # Validate sort parameter
        valid_sorts = {
            "rushing": "s.season_rushing_yards",
            "passing": "s.season_passing_yards", 
            "receiving": "s.season_receiving_yards",
            "name": "s.player_name"
        }
        order_by = valid_sorts.get(sort, "s.season_rushing_yards")
        
        # Validate order parameter
        if order.lower() not in ["asc", "desc"]:
            order = "desc"

        query = f"""
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
        ORDER BY {order_by} {order.upper()}
        LIMIT 25
        """
        rows = run_all(query)
        return render_template("players.html", players=rows,current_sort=sort,
        current_order=order)

    @app.route("/search")
    def search():
        query = request.args.get("q", "").strip()
        
        # Basic input validation - limit length and prevent obviously malicious input
        if len(query) > 100:
            query = query[:100]
        
        # Remove potentially dangerous characters (though parameterized queries protect us)
        query = query.replace('%', '').replace('_', '').replace(';', '').replace('--', '')
        
        if not query:
            return render_template("search.html", query=query, players=[], teams=[], coaches=[])

        # Search players
        players = run_all(
            """
            SELECT DISTINCT name, number
            FROM player
            WHERE name ILIKE %s
            ORDER BY name
            """,
            params=(f"%{query}%",)
        )

        # Search teams
        teams = run_all(
            """
            SELECT DISTINCT name
            FROM team
            WHERE name ILIKE %s
            ORDER BY name
            """,
            params=(f"%{query}%",)
        )

        # Search coaches
        coaches = run_all(
            """
            SELECT DISTINCT name, dob
            FROM coach
            WHERE name ILIKE %s
            ORDER BY name
            """,
            params=(f"%{query}%",)
        )

        return render_template("search.html", query=query, players=players, teams=teams, coaches=coaches)

    @app.route("/player/<name>/<int:number>")
    def player_stats(name, number):
        # Validate URL parameters
        if not name or len(name) > 100 or not isinstance(number, int) or number < 0 or number > 999:
            return render_template("error.html", message="Invalid player parameters"), 400
        # Get player info
        player = run_one(
            """
            SELECT name, number, dob, position, weight, height, war
            FROM player
            WHERE name = %s AND number = %s
            """,
            params=(name, number)
        )

        if not player:
            return render_template("error.html", message="Player not found"), 404

        # Get career stats (sum across seasons)
        career_stats = run_one(
            """
            SELECT
                SUM(season_rushing_yards) as total_rushing_yards,
                SUM(season_rushing_attempts) as total_rushing_attempts,
                SUM(season_rushing_touchdowns) as total_rushing_touchdowns,
                SUM(season_receiving_yards) as total_receiving_yards,
                SUM(season_receiving_attempts) as total_receiving_attempts,
                SUM(season_receiving_touchdowns) as total_receiving_touchdowns,
                SUM(season_passing_yards) as total_passing_yards,
                SUM(season_passing_attempts) as total_passing_attempts,
                SUM(season_passing_completions) as total_passing_completions,
                SUM(season_passing_touchdowns) as total_passing_touchdowns,
                SUM(season_offensive_interceptions) as total_offensive_interceptions,
                SUM(season_defensive_interceptions) as total_defensive_interceptions,
                SUM(season_offensive_sacks) as total_offensive_sacks,
                SUM(season_defensive_sacks) as total_defensive_sacks,
                SUM(season_tackles) as total_tackles,
                SUM(season_tackles_for_loss) as total_tackles_for_loss,
                SUM(season_forced_fumbles) as total_forced_fumbles,
                SUM(season_fumble_recoveries) as total_fumble_recoveries,
                SUM(season_special_teams_returns) as total_special_teams_returns,
                SUM(season_special_teams_touchdowns) as total_special_teams_touchdowns,
                SUM(season_special_teams_yards) as total_special_teams_yards,
                SUM(season_punting_yards) as total_punting_yards,
                SUM(season_punting_attempts) as total_punting_attempts,
                SUM(season_kicking_attempts) as total_kicking_attempts,
                SUM(season_kicking_made) as total_kicking_made,
                SUM(season_extra_point_attempts) as total_extra_point_attempts,
                SUM(season_extra_points_made) as total_extra_points_made
            FROM season_stats
            WHERE player_name = %s AND player_number = %s
            """,
            params=(name, number)
        )

        # Get teams played for
        teams = run_all(
            """
            SELECT DISTINCT t.name, pf.season
            FROM playsfor pf
            JOIN team t ON pf.team_id = t.team_id
            WHERE pf.player_name = %s AND pf.player_number = %s
            ORDER BY pf.season
            """,
            params=(name, number)
        )

        return render_template("player_stats.html", player=player, career_stats=career_stats, teams=teams)

    @app.route("/team/<name>")
    def team_stats(name):
        # Validate URL parameter
        if not name or len(name) > 100:
            return render_template("error.html", message="Invalid team name"), 400
        # Get team info
        team = run_one(
            """
            SELECT name, division, address, titles, president, tv_tag
            FROM team
            WHERE name = %s
            """,
            params=(name,)
        )

        if not team:
            return render_template("error.html", message="Team not found"), 404

        # Get current roster (latest season)
        roster = run_all(
            """
            SELECT p.name, p.number, p.position, pf.season
            FROM playsfor pf
            JOIN player p ON pf.player_name = p.name AND pf.player_number = p.number
            WHERE pf.team_id = (SELECT team_id FROM team WHERE name = %s)
            ORDER BY p.name
            """,
            params=(name,)
        )

        # Get coaches
        coaches = run_all(
            """
            SELECT c.name, cf.season
            FROM coachesfor cf
            JOIN coach c ON cf.coach_name = c.name AND cf.coach_dob = c.dob
            WHERE cf.team_id = (SELECT team_id FROM team WHERE name = %s)
            ORDER BY cf.season DESC, c.name
            """,
            params=(name,)
        )

        return render_template("team_stats.html", team=team, roster=roster, coaches=coaches)

    @app.route("/coach/<name>/<dob>")
    def coach_stats(name, dob):
        # Validate URL parameters
        if not name or len(name) > 100 or not dob or len(dob) > 20:
            return render_template("error.html", message="Invalid coach parameters"), 400
        # Get coach info
        coach = run_one(
            """
            SELECT name, dob, record
            FROM coach
            WHERE name = %s AND dob = %s
            """,
            params=(name, dob)
        )

        if not coach:
            return render_template("error.html", message="Coach not found"), 404

        # Get teams coached
        teams = run_all(
            """
            SELECT t.name, cf.season
            FROM coachesfor cf
            JOIN team t ON cf.team_id = t.team_id
            WHERE cf.coach_name = %s AND cf.coach_dob = %s
            ORDER BY cf.season DESC
            """,
            params=(name, dob)
        )

        return render_template("coach_stats.html", coach=coach, teams=teams)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
