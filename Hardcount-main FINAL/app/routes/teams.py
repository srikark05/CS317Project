from flask import Blueprint, render_template, request
from app import run_all, run_one

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/teams')
def index():
    rows = run_all("""
        SELECT
            t.team_id,
            t.name,
            t.division,
            t.address,
            t.titles,
            t.president,
            t.tv_tag,
            COUNT(DISTINCT pf.player_name) AS roster_size
        FROM team t
        LEFT JOIN playsfor pf ON pf.team_id = t.team_id
        GROUP BY t.team_id, t.name, t.division, t.address, t.titles, t.president, t.tv_tag
        ORDER BY t.name
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
            p.player_id,
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
        SELECT c.name, c.dob, c.record, cf.season
        FROM coachesfor cf
        JOIN coach c ON cf.coach_name = c.name AND cf.coach_dob = c.dob
        WHERE cf.team_id = %s
        ORDER BY cf.season DESC, c.name
    """, params=(team_id,))

    return render_template('teams/detail.html', team=team, roster=roster, coaches=coaches)