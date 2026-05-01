from flask import Blueprint, render_template, request
from app import run_all, run_one

coaches_bp = Blueprint('coaches', __name__)

@coaches_bp.route('/coaches')
def index():
    season = request.args.get('season', None)
    team = request.args.get('team', None)

    filters = ["st.head_coach IS NOT NULL", "st.head_coach NOT IN ('NR', '')"]
    params = []

    if season:
        filters.append("st.season = %s")
        params.append(season)
    if team:
        filters.append("t.team_id = %s")
        params.append(team)

    where = "WHERE " + " AND ".join(filters)

    rows = run_all(f"""
        SELECT
            st.head_coach   AS name,
            NULL            AS dob,
            NULL            AS record,
            st.team_name    AS team_name,
            t.team_id,
            st.season
        FROM staging_wnfc_teams st
        LEFT JOIN team t ON LOWER(TRIM(t.name)) = LOWER(TRIM(st.team_name))
        {where}
        ORDER BY st.season DESC, st.team_name ASC
    """, params=params if params else None)

    seasons = run_all("""
        SELECT DISTINCT season FROM staging_wnfc_teams
        WHERE head_coach IS NOT NULL AND head_coach NOT IN ('NR', '')
        ORDER BY season DESC
    """)

    teams = run_all("""
        SELECT DISTINCT ON (t.name) t.team_id, t.name FROM team t ORDER BY t.name, t.team_id
    """)

    return render_template('coaches/coaches.html',
        coaches=rows,
        seasons=seasons,
        teams=teams,
        current_season=season,
        current_team=team
    )

@coaches_bp.route('/coaches/<path:name>')
def detail(name):
    history = run_all("""
        SELECT
            st.season,
            st.team_name,
            t.team_id
        FROM staging_wnfc_teams st
        LEFT JOIN team t ON LOWER(TRIM(t.name)) = LOWER(TRIM(st.team_name))
        WHERE st.head_coach = %s
        ORDER BY st.season DESC
    """, params=(name,))

    coach = {'name': name, 'dob': None, 'record': None} if history else None

    return render_template('coaches/detail.html',
        coach=coach,
        history=history
    )