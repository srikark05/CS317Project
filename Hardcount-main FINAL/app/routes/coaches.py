from flask import Blueprint, render_template, request
from app import run_all, run_one

coaches_bp = Blueprint('coaches', __name__)

@coaches_bp.route('/coaches')
def index():
    season = request.args.get('season', None)
    team = request.args.get('team', None)

    filters = []
    params = []

    if season:
        filters.append("cf.season = %s")
        params.append(season)
    if team:
        filters.append("t.team_id = %s")
        params.append(team)

    where = "WHERE " + " AND ".join(filters) if filters else ""

    rows = run_all(f"""
        SELECT
            c.name,
            c.dob,
            c.record,
            t.name AS team_name,
            t.team_id,
            cf.season
        FROM coach c
        JOIN coachesfor cf
            ON cf.coach_name = c.name
           AND cf.coach_dob = c.dob
        JOIN team t ON t.team_id = cf.team_id
        {where}
        ORDER BY cf.season DESC, c.name ASC
    """, params=params if params else None)

    seasons = run_all("""
        SELECT DISTINCT season FROM coachesfor ORDER BY season DESC
    """)

    teams = run_all("""
        SELECT team_id, name FROM team ORDER BY name
    """)

    return render_template('coaches/coaches.html',
        coaches=rows,
        seasons=seasons,
        teams=teams,
        current_season=season,
        current_team=team
    )

@coaches_bp.route('/coaches/<string:name>/<string:dob>')
def detail(name, dob):
    coach = run_one("""
        SELECT
            c.name,
            c.dob,
            c.record
        FROM coach c
        WHERE c.name = %s
        AND c.dob = %s
    """, params=(name, dob))

    history = run_all("""
        SELECT
            cf.season,
            t.name AS team_name,
            t.team_id
        FROM coachesfor cf
        JOIN team t ON t.team_id = cf.team_id
        WHERE cf.coach_name = %s
        AND cf.coach_dob = %s
        ORDER BY cf.season DESC
    """, params=(name, dob))

    return render_template('coaches/detail.html',
        coach=coach,
        history=history
    )