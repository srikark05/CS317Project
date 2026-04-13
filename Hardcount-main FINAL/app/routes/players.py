from flask import Blueprint, render_template, request
from app import run_all, run_one

players_bp = Blueprint('players', __name__)

OFFENSE_POSITIONS = ('QB', 'RB', 'WR', 'TE', 'OL', 'OT', 'OG', 'OC', 'FB')
DEFENSE_POSITIONS = ('DL', 'DE', 'DT', 'LB', 'CB', 'SS', 'FS', 'DB', 'NT')
SPECIAL_POSITIONS = ('K', 'P', 'LS', 'KR', 'PR')

@players_bp.route('/players')
def index():
    group = request.args.get('group', 'all')
    sort = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    search_query = request.args.get('q', '').strip()

    sort_options = {
        "name":      "p.name",
        "rushing":   "ls.season_rushing_yards",
        "passing":   "ls.season_passing_yards",
        "receiving": "ls.season_receiving_yards",
    }

    order_by = sort_options.get(sort, "p.name")
    if order.lower() not in ("asc", "desc"):
        order = "asc"

    # build position filter
    params = []
    if group == 'offense':
        pos_filter = "AND p.position IN %s"
        params.append(OFFENSE_POSITIONS)
    elif group == 'defense':
        pos_filter = "AND p.position IN %s"
        params.append(DEFENSE_POSITIONS)
    elif group == 'special':
        pos_filter = "AND p.position IN %s"
        params.append(SPECIAL_POSITIONS)
    else:
        pos_filter = ""

    # build name search filter
    if search_query:
        name_filter = "AND p.name ILIKE %s"
        params.append(f"%{search_query}%")
    else:
        name_filter = ""

    # CTEs deduplicate so each player appears once (latest season only)
    query = f"""
        WITH latest_stats AS (
            SELECT DISTINCT ON (player_name, player_number)
                player_name, player_number, season,
                season_rushing_yards, season_passing_yards, season_receiving_yards,
                season_rushing_touchdowns, season_passing_touchdowns, season_tackles
            FROM season_stats
            ORDER BY player_name, player_number, season DESC NULLS LAST
        ),
        latest_team AS (
            SELECT DISTINCT ON (pf.player_name, pf.player_number)
                pf.player_name, pf.player_number, t.name AS team_name
            FROM playsfor pf
            JOIN team t ON t.team_id = pf.team_id
            ORDER BY pf.player_name, pf.player_number, pf.season DESC NULLS LAST
        )
        SELECT
            p.name AS player_name,
            p.number AS player_number,
            p.position,
            p.war,
            ls.season,
            COALESCE(lt.team_name, 'Unknown') AS team_name,
            COALESCE(ls.season_rushing_yards, 0) AS season_rushing_yards,
            COALESCE(ls.season_passing_yards, 0) AS season_passing_yards,
            COALESCE(ls.season_receiving_yards, 0) AS season_receiving_yards,
            COALESCE(ls.season_rushing_touchdowns, 0) AS season_rushing_touchdowns,
            COALESCE(ls.season_passing_touchdowns, 0) AS season_passing_touchdowns,
            COALESCE(ls.season_tackles, 0) AS season_tackles
        FROM player p
        LEFT JOIN latest_stats ls
            ON ls.player_name = p.name AND ls.player_number = p.number
        LEFT JOIN latest_team lt
            ON lt.player_name = p.name AND lt.player_number = p.number
        WHERE 1=1
        {pos_filter}
        {name_filter}
        ORDER BY {order_by} {order.upper()}
    """

    rows = run_all(query, params=tuple(params) if params else None)

    return render_template('players/players.html',
        players=rows,
        current_group=group,
        current_sort=sort,
        current_order=order,
        search_query=search_query
    )


@players_bp.route('/players/<string:name>/<int:number>')
def detail(name, number):
    player = run_one("""
        SELECT name, number, dob, position, weight, height, war
        FROM player
        WHERE name = %s AND number = %s
    """, params=(name, number))

    if not player:
        return render_template('error.html', message="Player not found"), 404

    season_stats = run_all("""
        SELECT
            season,
            season_rushing_yards, season_rushing_attempts, season_rushing_touchdowns,
            season_receiving_yards, season_receiving_attempts, season_receiving_touchdowns,
            season_passing_yards, season_passing_attempts, season_passing_completions, season_passing_touchdowns,
            season_tackles, season_defensive_sacks, season_defensive_interceptions,
            season_tackles_for_loss, season_forced_fumbles, season_fumble_recoveries
        FROM season_stats
        WHERE player_name = %s AND player_number = %s
        ORDER BY season DESC
    """, params=(name, number))

    teams = run_all("""
        SELECT DISTINCT t.name AS team_name, t.team_id, pf.season
        FROM playsfor pf
        JOIN team t ON pf.team_id = t.team_id
        WHERE pf.player_name = %s AND pf.player_number = %s
        ORDER BY pf.season DESC
    """, params=(name, number))

    return render_template('players/detail.html',
        player=player,
        season_stats=season_stats,
        teams=teams
    )

