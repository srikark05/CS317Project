
from flask import Blueprint, render_template, request
from app import run_all, run_one

games_bp = Blueprint('games', __name__)

@games_bp.route('/games')
def index():
    week = request.args.get('week', None)
    season = request.args.get('season', None)

    filters = []
    params = []

    if week:
        filters.append("g.week = %s")
        params.append(week)
    if season:
        filters.append("g.season = %s")
        params.append(season)

    where = "WHERE " + " AND ".join(filters) if filters else ""

    rows = run_all(f"""
        SELECT
            g.week,
            g.season,
            g.play_date,
            g.score,
            g.address,
            ht.name AS home_team_name,
            at.name AS away_team_name
        FROM games g
        JOIN team ht ON ht.team_id = g.home_team
        JOIN team at ON at.team_id = g.away_team
        {where}
        ORDER BY g.season DESC, g.week ASC
    """, params=params if params else None)

    weeks = run_all("""
        SELECT DISTINCT week FROM games ORDER BY week ASC
    """)
    seasons = run_all("""
        SELECT DISTINCT season FROM games ORDER BY season DESC
    """)

    return render_template('games/games.html',
        games=rows,
        weeks=weeks,
        seasons=seasons,
        current_week=week,
        current_season=season
    )

@games_bp.route('/games/<int:season>/<int:week>/<int:home_team>')
def detail(season, week, home_team):
    game = run_one("""
        SELECT
            g.week,
            g.season,
            g.play_date,
            g.score,
            g.address,
            ht.name AS home_team_name,
            at.name AS away_team_name
        FROM games g
        JOIN team ht ON ht.team_id = g.home_team
        JOIN team at ON at.team_id = g.away_team
        WHERE g.season = %s AND g.week = %s AND g.home_team = %s
    """, params=(season, week, home_team))

    stat_leaders = run_all("""
        SELECT
            pi.player_name,
            pi.player_number,
            pi.game_rushing_yards,
            pi.game_passing_yards,
            pi.game_receiving_yards,
            pi.game_passing_touchdowns,
            pi.game_rushing_touchdowns,
            pi.game_receiving_touchdowns,
            COALESCE(t.name, 'Unknown') AS team_name
        FROM played_in pi
        LEFT JOIN playsfor pf
            ON pf.player_name = pi.player_name
           AND pf.player_number = pi.player_number
           AND pf.season = %s
        LEFT JOIN team t ON t.team_id = pf.team_id
        WHERE pi.game_date = %s AND pi.home_team = %s
        ORDER BY pi.game_passing_yards DESC
    """, params=(season, game['play_date'], home_team) if game else None)

    return render_template('games/detail.html',
        game=game,
        stat_leaders=stat_leaders
    )