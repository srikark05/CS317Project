from flask import Blueprint, render_template, request
from app import run_all, run_one

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/teams')
def index():
    rows = run_all("""
        SELECT DISTINCT ON (t.name)
            t.team_id,
            t.name,
            t.division,
            t.address,
            t.titles,
            t.president,
            t.tv_tag,
            (SELECT COUNT(DISTINCT pf.player_name)
             FROM playsfor pf WHERE pf.team_id = t.team_id) AS roster_size
        FROM team t
        ORDER BY t.name, (t.division IS NOT NULL) DESC, t.team_id
    """)
    return render_template('teams/teams.html', teams=rows)

@teams_bp.route('/teams/<int:team_id>')
def detail(team_id):
    team = run_one("""
        SELECT *
        FROM team
        WHERE team_id = %s
    """, params=(team_id,))

    roster = run_all("""
        SELECT
            p.name,
            p.number,
            p.position,
            pf.season
        FROM playsfor pf
        JOIN player p
            ON p.name = pf.player_name
           AND p.number = pf.player_number
        WHERE pf.team_id = %s
        ORDER BY pf.season DESC, p.name
    """, params=(team_id,))

    coaches = run_all("""
        SELECT st.head_coach AS name, NULL AS dob, NULL AS record, st.season
        FROM staging_wnfc_teams st
        JOIN team t ON LOWER(TRIM(t.name)) = LOWER(TRIM(st.team_name))
        WHERE t.team_id = %s
          AND st.head_coach IS NOT NULL AND st.head_coach NOT IN ('NR', '')
        ORDER BY st.season DESC, st.head_coach
    """, params=(team_id,))

    return render_template('teams/detail.html', team=team, roster=roster, coaches=coaches)