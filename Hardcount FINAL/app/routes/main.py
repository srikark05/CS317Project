from flask import Blueprint, render_template, request
from app import run_one, run_all

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    recent_games = run_all("""
        SELECT
            g.week,
            g.season,
            g.play_date,
            g.score,
            ht.name AS home_team_name,
            ht.team_id AS home_team_id,
            at.name AS away_team_name,
            at.team_id AS away_team_id
        FROM games g
        JOIN team ht ON ht.team_id = g.home_team
        JOIN team at ON at.team_id = g.away_team
        WHERE g.score IS NOT NULL AND g.score <> ''
        ORDER BY g.season DESC, g.week DESC
        LIMIT 5
    """)

    top_standings = run_all("""
        WITH latest AS (
            SELECT MAX(season) AS s FROM staging_wnfc_teams
        ),
        ranked AS (
            SELECT
                st.team_name,
                st.division,
                st.pct,
                (COALESCE(st.home_wins, 0) + COALESCE(st.road_win, 0))   AS wins,
                (COALESCE(st.home_loss, 0) + COALESCE(st.road_loss, 0)) AS losses,
                (COALESCE(st.home_ties, 0) + COALESCE(st.road_tie, 0))  AS ties,
                t.team_id,
                ROW_NUMBER() OVER (
                    PARTITION BY st.division
                    ORDER BY COALESCE(st.pct, 0) DESC,
                             (COALESCE(st.home_wins, 0) + COALESCE(st.road_win, 0)) DESC
                ) AS rn
            FROM staging_wnfc_teams st
            LEFT JOIN team t ON LOWER(TRIM(t.name)) = LOWER(TRIM(st.team_name))
            WHERE st.season = (SELECT s FROM latest)
        )
        SELECT * FROM ranked WHERE rn <= 3
        ORDER BY division ASC, rn ASC
    """)

    return render_template('index.html', recent_games=recent_games, top_standings=top_standings)


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

