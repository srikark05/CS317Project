import os
from contextlib import contextmanager
from functools import wraps

from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg
from psycopg.rows import dict_row


def create_app() -> Flask:
    app = Flask(__name__)
    
    # Session configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    Session(app)

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

    # Admin authentication decorator
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'admin' not in session or not session['admin']:
                flash('Please log in as administrator to access this page.', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    # Login route
    @app.route("/login", methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            password = request.form.get('password', '').strip()
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin')  # Change this in production!
            
            # For simplicity, using plaintext comparison with env variable
            # In production, store hashed passwords in database and use check_password_hash()
            if password == admin_password:
                session['admin'] = True
                session.permanent = True
                flash('Successfully logged in as administrator.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid password. Please try again.', 'error')
        
        return render_template('login.html')

    # Logout route
    @app.route("/logout")
    def logout():
        session.clear()
        flash('You have been logged out.', 'success')
        return redirect(url_for('index'))

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

    # ===== ADMIN ROUTES (Protected) =====
    
    @app.route("/admin", methods=['GET'])
    @admin_required
    def admin_dashboard():
        """Admin dashboard with data management options"""
        return render_template("admin_dashboard.html")

    @app.route("/admin/add-game", methods=['GET', 'POST'])
    @admin_required
    def add_game():
        """Add a new game with coaches and player stats"""
        
        # Get available teams and coaches for the form
        teams = run_all("SELECT team_id, name FROM team ORDER BY name")
        coaches = run_all("SELECT name, dob FROM coach ORDER BY name")
        
        if request.method == 'POST':
            try:
                # Get form data
                home_team_id = request.form.get('home_team_id', '').strip()
                away_team_id = request.form.get('away_team_id', '').strip()
                home_coach_name = request.form.get('home_coach_name', '').strip()
                home_coach_dob = request.form.get('home_coach_dob', '').strip()
                away_coach_name = request.form.get('away_coach_name', '').strip()
                away_coach_dob = request.form.get('away_coach_dob', '').strip()
                game_date = request.form.get('game_date', '').strip()
                week = request.form.get('week', '').strip()
                season = request.form.get('season', '').strip()
                score = request.form.get('score', '').strip()
                address = request.form.get('address', '').strip()
                
                # Validate basic data
                if not all([home_team_id, away_team_id, home_coach_name, away_coach_name, 
                           game_date, week, season]):
                    flash('Missing required fields.', 'error')
                    return render_template('add_game.html', teams=teams, coaches=coaches)
                
                home_team_id = int(home_team_id)
                away_team_id = int(away_team_id)
                week = int(week)
                season = int(season)
                
                if home_team_id == away_team_id:
                    flash('Home and away teams must be different.', 'error')
                    return render_template('add_game.html', teams=teams, coaches=coaches)
                
                # Ensure coaches exist in database
                for coach_name, coach_dob in [(home_coach_name, home_coach_dob), 
                                               (away_coach_name, away_coach_dob)]:
                    run_all(
                        """INSERT INTO coach (name, dob) 
                           SELECT %s, %s 
                           WHERE NOT EXISTS (SELECT 1 FROM coach WHERE name = %s AND dob = %s)""",
                        params=(coach_name, coach_dob, coach_name, coach_dob)
                    )
                
                # Ensure coaches are linked to teams for the season
                run_all(
                    """INSERT INTO coachesfor (coach_name, coach_dob, team_id, season)
                       SELECT %s, %s, %s, %s
                       WHERE NOT EXISTS (SELECT 1 FROM coachesfor 
                                       WHERE coach_name = %s AND coach_dob = %s 
                                       AND team_id = %s AND season = %s)""",
                    params=(home_coach_name, home_coach_dob, home_team_id, season,
                           home_coach_name, home_coach_dob, home_team_id, season)
                )
                run_all(
                    """INSERT INTO coachesfor (coach_name, coach_dob, team_id, season)
                       SELECT %s, %s, %s, %s
                       WHERE NOT EXISTS (SELECT 1 FROM coachesfor 
                                       WHERE coach_name = %s AND coach_dob = %s 
                                       AND team_id = %s AND season = %s)""",
                    params=(away_coach_name, away_coach_dob, away_team_id, season,
                           away_coach_name, away_coach_dob, away_team_id, season)
                )
                
                # Insert game
                run_all(
                    """INSERT INTO games (week, season, play_date, address, score, home_team, away_team)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    params=(week, season, game_date, address, score, home_team_id, away_team_id)
                )
                
                # Process player stats for home team
                player_keys = [k for k in request.form.keys() if k.startswith('home_player_')]
                for player_key in player_keys:
                    parts = player_key.split('_')
                    if parts[-1] == 'name':
                        player_idx = '_'.join(parts[2:-1])
                        player_name = request.form.get(f'home_player_{player_idx}_name', '').strip()
                        player_number = request.form.get(f'home_player_{player_idx}_number', '').strip()
                        
                        if player_name and player_number:
                            player_number = int(player_number)
                            
                            # Collect all stat fields for this player
                            stats = {}
                            stat_fields = ['rushing_yards', 'rushing_attempts', 'rushing_touchdowns',
                                         'receiving_yards', 'receiving_attempts', 'receiving_touchdowns',
                                         'passing_yards', 'passing_attempts', 'passing_completions',
                                         'passing_touchdowns', 'offensive_interceptions', 'defensive_interceptions',
                                         'offensive_sacks', 'defensive_sacks', 'tackles', 'tackles_for_loss',
                                         'forced_fumbles', 'fumble_recoveries', 'special_teams_returns',
                                         'special_teams_touchdowns', 'special_teams_yards', 'punting_yards',
                                         'punting_attempts', 'kicking_attempts', 'kicking_made',
                                         'extra_point_attempts', 'extra_points_made']
                            
                            for stat_field in stat_fields:
                                val = request.form.get(f'home_player_{player_idx}_{stat_field}', '0').strip()
                                stats[stat_field] = int(val) if val and val.isdigit() else 0
                            
                            # Insert into played_in
                            run_all(
                                """INSERT INTO played_in 
                                   (player_name, player_number, game_date, week, season, home_team,
                                    game_rushing_yards, game_rushing_attempts, game_rushing_touchdowns,
                                    game_receiving_yards, game_receiving_attempts, game_receiving_touchdowns,
                                    game_passing_yards, game_passing_attempts, game_passing_completions,
                                    game_passing_touchdowns, game_offensive_interceptions, game_defensive_interceptions,
                                    game_offensive_sacks, game_defensive_sacks, game_tackles, game_tackles_for_loss,
                                    game_forced_fumbles, game_fumble_recoveries, game_special_teams_returns,
                                    game_special_teams_touchdowns, game_special_teams_yards, game_punting_yards,
                                    game_punting_attempts, game_kicking_attempts, game_kicking_made,
                                    game_extra_point_attempts, game_extra_points_made)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                params=(player_name, player_number, game_date, week, season, home_team_id,
                                       stats['rushing_yards'], stats['rushing_attempts'], stats['rushing_touchdowns'],
                                       stats['receiving_yards'], stats['receiving_attempts'], stats['receiving_touchdowns'],
                                       stats['passing_yards'], stats['passing_attempts'], stats['passing_completions'],
                                       stats['passing_touchdowns'], stats['offensive_interceptions'], stats['defensive_interceptions'],
                                       stats['offensive_sacks'], stats['defensive_sacks'], stats['tackles'], stats['tackles_for_loss'],
                                       stats['forced_fumbles'], stats['fumble_recoveries'], stats['special_teams_returns'],
                                       stats['special_teams_touchdowns'], stats['special_teams_yards'], stats['punting_yards'],
                                       stats['punting_attempts'], stats['kicking_attempts'], stats['kicking_made'],
                                       stats['extra_point_attempts'], stats['extra_points_made'])
                            )
                            
                            # Update season_stats by aggregating all games for this player-season
                            run_all(
                                """INSERT INTO season_stats 
                                   (player_name, player_number, season, season_rushing_yards, season_rushing_attempts,
                                    season_rushing_touchdowns, season_receiving_yards, season_receiving_attempts,
                                    season_receiving_touchdowns, season_passing_yards, season_passing_attempts,
                                    season_passing_completions, season_passing_touchdowns, season_offensive_interceptions,
                                    season_defensive_interceptions, season_offensive_sacks, season_defensive_sacks,
                                    season_tackles, season_tackles_for_loss, season_forced_fumbles, season_fumble_recoveries,
                                    season_special_teams_returns, season_special_teams_touchdowns, season_special_teams_yards,
                                    season_punting_yards, season_punting_attempts, season_kicking_attempts, season_kicking_made,
                                    season_extra_point_attempts, season_extra_points_made)
                                   SELECT %s, %s, %s,
                                    COALESCE(SUM(game_rushing_yards), 0),
                                    COALESCE(SUM(game_rushing_attempts), 0),
                                    COALESCE(SUM(game_rushing_touchdowns), 0),
                                    COALESCE(SUM(game_receiving_yards), 0),
                                    COALESCE(SUM(game_receiving_attempts), 0),
                                    COALESCE(SUM(game_receiving_touchdowns), 0),
                                    COALESCE(SUM(game_passing_yards), 0),
                                    COALESCE(SUM(game_passing_attempts), 0),
                                    COALESCE(SUM(game_passing_completions), 0),
                                    COALESCE(SUM(game_passing_touchdowns), 0),
                                    COALESCE(SUM(game_offensive_interceptions), 0),
                                    COALESCE(SUM(game_defensive_interceptions), 0),
                                    COALESCE(SUM(game_offensive_sacks), 0),
                                    COALESCE(SUM(game_defensive_sacks), 0),
                                    COALESCE(SUM(game_tackles), 0),
                                    COALESCE(SUM(game_tackles_for_loss), 0),
                                    COALESCE(SUM(game_forced_fumbles), 0),
                                    COALESCE(SUM(game_fumble_recoveries), 0),
                                    COALESCE(SUM(game_special_teams_returns), 0),
                                    COALESCE(SUM(game_special_teams_touchdowns), 0),
                                    COALESCE(SUM(game_special_teams_yards), 0),
                                    COALESCE(SUM(game_punting_yards), 0),
                                    COALESCE(SUM(game_punting_attempts), 0),
                                    COALESCE(SUM(game_kicking_attempts), 0),
                                    COALESCE(SUM(game_kicking_made), 0),
                                    COALESCE(SUM(game_extra_point_attempts), 0),
                                    COALESCE(SUM(game_extra_points_made), 0)
                                   FROM played_in
                                   WHERE player_name = %s AND player_number = %s AND season = %s
                                   ON CONFLICT (player_name, player_number, season) DO UPDATE SET
                                    season_rushing_yards = EXCLUDED.season_rushing_yards,
                                    season_rushing_attempts = EXCLUDED.season_rushing_attempts,
                                    season_rushing_touchdowns = EXCLUDED.season_rushing_touchdowns,
                                    season_receiving_yards = EXCLUDED.season_receiving_yards,
                                    season_receiving_attempts = EXCLUDED.season_receiving_attempts,
                                    season_receiving_touchdowns = EXCLUDED.season_receiving_touchdowns,
                                    season_passing_yards = EXCLUDED.season_passing_yards,
                                    season_passing_attempts = EXCLUDED.season_passing_attempts,
                                    season_passing_completions = EXCLUDED.season_passing_completions,
                                    season_passing_touchdowns = EXCLUDED.season_passing_touchdowns,
                                    season_offensive_interceptions = EXCLUDED.season_offensive_interceptions,
                                    season_defensive_interceptions = EXCLUDED.season_defensive_interceptions,
                                    season_offensive_sacks = EXCLUDED.season_offensive_sacks,
                                    season_defensive_sacks = EXCLUDED.season_defensive_sacks,
                                    season_tackles = EXCLUDED.season_tackles,
                                    season_tackles_for_loss = EXCLUDED.season_tackles_for_loss,
                                    season_forced_fumbles = EXCLUDED.season_forced_fumbles,
                                    season_fumble_recoveries = EXCLUDED.season_fumble_recoveries,
                                    season_special_teams_returns = EXCLUDED.season_special_teams_returns,
                                    season_special_teams_touchdowns = EXCLUDED.season_special_teams_touchdowns,
                                    season_special_teams_yards = EXCLUDED.season_special_teams_yards,
                                    season_punting_yards = EXCLUDED.season_punting_yards,
                                    season_punting_attempts = EXCLUDED.season_punting_attempts,
                                    season_kicking_attempts = EXCLUDED.season_kicking_attempts,
                                    season_kicking_made = EXCLUDED.season_kicking_made,
                                    season_extra_point_attempts = EXCLUDED.season_extra_point_attempts,
                                    season_extra_points_made = EXCLUDED.season_extra_points_made""",
                                params=(player_name, player_number, season, player_name, player_number, season)
                            )
                
                # Process player stats for away team (same logic)
                player_keys = [k for k in request.form.keys() if k.startswith('away_player_')]
                for player_key in player_keys:
                    parts = player_key.split('_')
                    if parts[-1] == 'name':
                        player_idx = '_'.join(parts[2:-1])
                        player_name = request.form.get(f'away_player_{player_idx}_name', '').strip()
                        player_number = request.form.get(f'away_player_{player_idx}_number', '').strip()
                        
                        if player_name and player_number:
                            player_number = int(player_number)
                            
                            stats = {}
                            stat_fields = ['rushing_yards', 'rushing_attempts', 'rushing_touchdowns',
                                         'receiving_yards', 'receiving_attempts', 'receiving_touchdowns',
                                         'passing_yards', 'passing_attempts', 'passing_completions',
                                         'passing_touchdowns', 'offensive_interceptions', 'defensive_interceptions',
                                         'offensive_sacks', 'defensive_sacks', 'tackles', 'tackles_for_loss',
                                         'forced_fumbles', 'fumble_recoveries', 'special_teams_returns',
                                         'special_teams_touchdowns', 'special_teams_yards', 'punting_yards',
                                         'punting_attempts', 'kicking_attempts', 'kicking_made',
                                         'extra_point_attempts', 'extra_points_made']
                            
                            for stat_field in stat_fields:
                                val = request.form.get(f'away_player_{player_idx}_{stat_field}', '0').strip()
                                stats[stat_field] = int(val) if val and val.isdigit() else 0
                            
                            run_all(
                                """INSERT INTO played_in 
                                   (player_name, player_number, game_date, week, season, home_team,
                                    game_rushing_yards, game_rushing_attempts, game_rushing_touchdowns,
                                    game_receiving_yards, game_receiving_attempts, game_receiving_touchdowns,
                                    game_passing_yards, game_passing_attempts, game_passing_completions,
                                    game_passing_touchdowns, game_offensive_interceptions, game_defensive_interceptions,
                                    game_offensive_sacks, game_defensive_sacks, game_tackles, game_tackles_for_loss,
                                    game_forced_fumbles, game_fumble_recoveries, game_special_teams_returns,
                                    game_special_teams_touchdowns, game_special_teams_yards, game_punting_yards,
                                    game_punting_attempts, game_kicking_attempts, game_kicking_made,
                                    game_extra_point_attempts, game_extra_points_made)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                params=(player_name, player_number, game_date, week, season, home_team_id,
                                       stats['rushing_yards'], stats['rushing_attempts'], stats['rushing_touchdowns'],
                                       stats['receiving_yards'], stats['receiving_attempts'], stats['receiving_touchdowns'],
                                       stats['passing_yards'], stats['passing_attempts'], stats['passing_completions'],
                                       stats['passing_touchdowns'], stats['offensive_interceptions'], stats['defensive_interceptions'],
                                       stats['offensive_sacks'], stats['defensive_sacks'], stats['tackles'], stats['tackles_for_loss'],
                                       stats['forced_fumbles'], stats['fumble_recoveries'], stats['special_teams_returns'],
                                       stats['special_teams_touchdowns'], stats['special_teams_yards'], stats['punting_yards'],
                                       stats['punting_attempts'], stats['kicking_attempts'], stats['kicking_made'],
                                       stats['extra_point_attempts'], stats['extra_points_made'])
                            )
                            
                            run_all(
                                """INSERT INTO season_stats 
                                   (player_name, player_number, season, season_rushing_yards, season_rushing_attempts,
                                    season_rushing_touchdowns, season_receiving_yards, season_receiving_attempts,
                                    season_receiving_touchdowns, season_passing_yards, season_passing_attempts,
                                    season_passing_completions, season_passing_touchdowns, season_offensive_interceptions,
                                    season_defensive_interceptions, season_offensive_sacks, season_defensive_sacks,
                                    season_tackles, season_tackles_for_loss, season_forced_fumbles, season_fumble_recoveries,
                                    season_special_teams_returns, season_special_teams_touchdowns, season_special_teams_yards,
                                    season_punting_yards, season_punting_attempts, season_kicking_attempts, season_kicking_made,
                                    season_extra_point_attempts, season_extra_points_made)
                                   SELECT %s, %s, %s,
                                    COALESCE(SUM(game_rushing_yards), 0),
                                    COALESCE(SUM(game_rushing_attempts), 0),
                                    COALESCE(SUM(game_rushing_touchdowns), 0),
                                    COALESCE(SUM(game_receiving_yards), 0),
                                    COALESCE(SUM(game_receiving_attempts), 0),
                                    COALESCE(SUM(game_receiving_touchdowns), 0),
                                    COALESCE(SUM(game_passing_yards), 0),
                                    COALESCE(SUM(game_passing_attempts), 0),
                                    COALESCE(SUM(game_passing_completions), 0),
                                    COALESCE(SUM(game_passing_touchdowns), 0),
                                    COALESCE(SUM(game_offensive_interceptions), 0),
                                    COALESCE(SUM(game_defensive_interceptions), 0),
                                    COALESCE(SUM(game_offensive_sacks), 0),
                                    COALESCE(SUM(game_defensive_sacks), 0),
                                    COALESCE(SUM(game_tackles), 0),
                                    COALESCE(SUM(game_tackles_for_loss), 0),
                                    COALESCE(SUM(game_forced_fumbles), 0),
                                    COALESCE(SUM(game_fumble_recoveries), 0),
                                    COALESCE(SUM(game_special_teams_returns), 0),
                                    COALESCE(SUM(game_special_teams_touchdowns), 0),
                                    COALESCE(SUM(game_special_teams_yards), 0),
                                    COALESCE(SUM(game_punting_yards), 0),
                                    COALESCE(SUM(game_punting_attempts), 0),
                                    COALESCE(SUM(game_kicking_attempts), 0),
                                    COALESCE(SUM(game_kicking_made), 0),
                                    COALESCE(SUM(game_extra_point_attempts), 0),
                                    COALESCE(SUM(game_extra_points_made), 0)
                                   FROM played_in
                                   WHERE player_name = %s AND player_number = %s AND season = %s
                                   ON CONFLICT (player_name, player_number, season) DO UPDATE SET
                                    season_rushing_yards = EXCLUDED.season_rushing_yards,
                                    season_rushing_attempts = EXCLUDED.season_rushing_attempts,
                                    season_rushing_touchdowns = EXCLUDED.season_rushing_touchdowns,
                                    season_receiving_yards = EXCLUDED.season_receiving_yards,
                                    season_receiving_attempts = EXCLUDED.season_receiving_attempts,
                                    season_receiving_touchdowns = EXCLUDED.season_receiving_touchdowns,
                                    season_passing_yards = EXCLUDED.season_passing_yards,
                                    season_passing_attempts = EXCLUDED.season_passing_attempts,
                                    season_passing_completions = EXCLUDED.season_passing_completions,
                                    season_passing_touchdowns = EXCLUDED.season_passing_touchdowns,
                                    season_offensive_interceptions = EXCLUDED.season_offensive_interceptions,
                                    season_defensive_interceptions = EXCLUDED.season_defensive_interceptions,
                                    season_offensive_sacks = EXCLUDED.season_offensive_sacks,
                                    season_defensive_sacks = EXCLUDED.season_defensive_sacks,
                                    season_tackles = EXCLUDED.season_tackles,
                                    season_tackles_for_loss = EXCLUDED.season_tackles_for_loss,
                                    season_forced_fumbles = EXCLUDED.season_forced_fumbles,
                                    season_fumble_recoveries = EXCLUDED.season_fumble_recoveries,
                                    season_special_teams_returns = EXCLUDED.season_special_teams_returns,
                                    season_special_teams_touchdowns = EXCLUDED.season_special_teams_touchdowns,
                                    season_special_teams_yards = EXCLUDED.season_special_teams_yards,
                                    season_punting_yards = EXCLUDED.season_punting_yards,
                                    season_punting_attempts = EXCLUDED.season_punting_attempts,
                                    season_kicking_attempts = EXCLUDED.season_kicking_attempts,
                                    season_kicking_made = EXCLUDED.season_kicking_made,
                                    season_extra_point_attempts = EXCLUDED.season_extra_point_attempts,
                                    season_extra_points_made = EXCLUDED.season_extra_points_made""",
                                params=(player_name, player_number, season, player_name, player_number, season)
                            )
                
                flash('Game added successfully! All player and coach stats have been updated.', 'success')
                return redirect(url_for('admin_dashboard'))
            except Exception as e:
                app.logger.exception("Error adding game: %s", e)
                flash(f'Error adding game to database: {str(e)}', 'error')
        
        return render_template('add_game.html', teams=teams, coaches=coaches)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
