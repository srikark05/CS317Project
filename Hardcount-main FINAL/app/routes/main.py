from flask import Blueprint, render_template, request
from app import run_one, run_all

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    stats = run_one("""
        SELECT
            (SELECT COUNT(*) FROM team) AS teams,
            (SELECT COUNT(*) FROM player) AS players,
            (SELECT COUNT(*) FROM season_stats) AS season_rows
    """)

    if stats is None:
        stats = {"teams": 0, "players": 0, "season_rows": 0}

    return render_template('index.html', stats=stats)


@main_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()[:100]

    if not query:
        return render_template('search.html', query=query, players=[], teams=[], coaches=[])

    like = f"%{query}%"

    players = run_all("""
        SELECT DISTINCT name, number, position
        FROM player
        WHERE name ILIKE %s
        ORDER BY name
    """, params=(like,))

    teams = run_all("""
        SELECT DISTINCT team_id, name
        FROM team
        WHERE name ILIKE %s
        ORDER BY name
    """, params=(like,))

    coaches = run_all("""
        SELECT DISTINCT name, dob
        FROM coach
        WHERE name ILIKE %s
        ORDER BY name
    """, params=(like,))

    return render_template('search.html', query=query, players=players, teams=teams, coaches=coaches)

