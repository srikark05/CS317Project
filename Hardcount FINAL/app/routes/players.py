from flask import Blueprint, render_template, request
from app import run_all, run_one

players_bp = Blueprint('players', __name__)

OFFENSE_POSITIONS = ('QB', 'RB', 'WR', 'TE', 'OL', 'OT', 'OG', 'OC', 'FB')
DEFENSE_POSITIONS = ('DL', 'DE', 'DT', 'LB', 'CB', 'SS', 'FS', 'DB', 'NT')
SPECIAL_POSITIONS = ('K', 'P', 'LS', 'KR', 'PR')

def _int_param(key):
    try:
        return int(request.args.get(key, ''))
    except (ValueError, TypeError):
        return None

@players_bp.route('/players')
def index():
    group        = request.args.get('group', 'all')
    sort         = request.args.get('sort', 'war')
    order        = request.args.get('order', 'desc')
    search_query = request.args.get('q', '').strip()
    season       = _int_param('season')
    team_id      = _int_param('team_id')
    min_height   = _int_param('min_height')
    min_rush     = _int_param('min_rush')
    min_pass     = _int_param('min_pass')
    min_rec      = _int_param('min_rec')
    min_rush_td  = _int_param('min_rush_td')
    min_pass_td  = _int_param('min_pass_td')
    min_rec_td   = _int_param('min_rec_td')
    min_tackles  = _int_param('min_tackles')
    min_sacks    = _int_param('min_sacks')
    min_int      = _int_param('min_int')
    min_tfl      = _int_param('min_tfl')

    sort_options = {
        'name':             'p.name',
        'war':              'COALESCE(ls.season_war, 0)',
        'rushing':          'COALESCE(ls.season_rushing_yards, 0)',
        'rush_att':         'COALESCE(ls.season_rushing_attempts, 0)',
        'rush_td':          'COALESCE(ls.season_rushing_touchdowns, 0)',
        'passing':          'COALESCE(ls.season_passing_yards, 0)',
        'pass_att':         'COALESCE(ls.season_passing_attempts, 0)',
        'pass_td':          'COALESCE(ls.season_passing_touchdowns, 0)',
        'receiving':        'COALESCE(ls.season_receiving_yards, 0)',
        'rec':              'COALESCE(ls.season_receiving_attempts, 0)',
        'rec_td':           'COALESCE(ls.season_receiving_touchdowns, 0)',
        'tackles':          'COALESCE(ls.season_tackles, 0)',
        'sacks':            'COALESCE(ls.season_defensive_sacks, 0)',
        'interceptions':    'COALESCE(ls.season_defensive_interceptions, 0)',
        'tfl':              'COALESCE(ls.season_tackles_for_loss, 0)',
        'forced_fumbles':   'COALESCE(ls.season_forced_fumbles, 0)',
        'fumble_recoveries':'COALESCE(ls.season_fumble_recoveries, 0)',
        'st_returns':       'COALESCE(ls.season_special_teams_returns, 0)',
        'st_yards':         'COALESCE(ls.season_special_teams_yards, 0)',
        'st_td':            'COALESCE(ls.season_special_teams_touchdowns, 0)',
        'punt_att':         'COALESCE(ls.season_punting_attempts, 0)',
        'punt_yds':         'COALESCE(ls.season_punting_yards, 0)',
        'fg_made':          'COALESCE(ls.season_kicking_made, 0)',
        'fg_att':           'COALESCE(ls.season_kicking_attempts, 0)',
        'xp_made':          'COALESCE(ls.season_extra_points_made, 0)',
        'xp_att':           'COALESCE(ls.season_extra_point_attempts, 0)',
    }

    order_by = sort_options.get(sort, 'p.name')
    if order.lower() not in ('asc', 'desc'):
        order = 'asc'

    params = []

    if season:
        stats_cte = """
            SELECT DISTINCT ON (player_name)
                player_name, player_number, season,
                season_rushing_yards, season_rushing_attempts, season_rushing_touchdowns,
                season_passing_yards, season_passing_attempts, season_passing_completions, season_passing_touchdowns,
                season_receiving_yards, season_receiving_attempts, season_receiving_touchdowns,
                season_tackles, season_defensive_sacks, season_defensive_interceptions,
                season_tackles_for_loss, season_forced_fumbles, season_fumble_recoveries,
                season_special_teams_returns, season_special_teams_yards, season_special_teams_touchdowns,
                season_punting_yards, season_punting_attempts,
                season_kicking_attempts, season_kicking_made,
                season_extra_point_attempts, season_extra_points_made,
                season_war
            FROM season_stats
            WHERE season = %s
            ORDER BY player_name
        """
        params.append(season)
    else:
        stats_cte = """
            SELECT DISTINCT ON (player_name)
                player_name, player_number, season,
                season_rushing_yards, season_rushing_attempts, season_rushing_touchdowns,
                season_passing_yards, season_passing_attempts, season_passing_completions, season_passing_touchdowns,
                season_receiving_yards, season_receiving_attempts, season_receiving_touchdowns,
                season_tackles, season_defensive_sacks, season_defensive_interceptions,
                season_tackles_for_loss, season_forced_fumbles, season_fumble_recoveries,
                season_special_teams_returns, season_special_teams_yards, season_special_teams_touchdowns,
                season_punting_yards, season_punting_attempts,
                season_kicking_attempts, season_kicking_made,
                season_extra_point_attempts, season_extra_points_made,
                season_war
            FROM season_stats
            ORDER BY player_name, season DESC NULLS LAST
        """

    if group == 'offense':
        pos_filter = 'AND p.position = ANY(%s)'
        params.append(list(OFFENSE_POSITIONS))
    elif group == 'defense':
        pos_filter = 'AND p.position = ANY(%s)'
        params.append(list(DEFENSE_POSITIONS))
    elif group == 'special':
        pos_filter = 'AND p.position = ANY(%s)'
        params.append(list(SPECIAL_POSITIONS))
    else:
        pos_filter = ''

    if search_query:
        name_filter = 'AND p.name ILIKE %s'
        params.append(f'%{search_query}%')
    else:
        name_filter = ''

    season_join_filter = 'AND ls.player_name IS NOT NULL' if season else ''

    where_clauses = []
    if team_id:
        where_clauses.append('AND lt.team_id = %s')
        params.append(team_id)
    if min_height is not None and min_height > 0:
        where_clauses.append('AND p.height >= %s')
        params.append(min_height)
    if min_rush is not None and min_rush > 0:
        where_clauses.append('AND COALESCE(ls.season_rushing_yards, 0) >= %s')
        params.append(min_rush)
    if min_pass is not None and min_pass > 0:
        where_clauses.append('AND COALESCE(ls.season_passing_yards, 0) >= %s')
        params.append(min_pass)
    if min_rec is not None and min_rec > 0:
        where_clauses.append('AND COALESCE(ls.season_receiving_yards, 0) >= %s')
        params.append(min_rec)
    if min_rush_td is not None and min_rush_td > 0:
        where_clauses.append('AND COALESCE(ls.season_rushing_touchdowns, 0) >= %s')
        params.append(min_rush_td)
    if min_pass_td is not None and min_pass_td > 0:
        where_clauses.append('AND COALESCE(ls.season_passing_touchdowns, 0) >= %s')
        params.append(min_pass_td)
    if min_rec_td is not None and min_rec_td > 0:
        where_clauses.append('AND COALESCE(ls.season_receiving_touchdowns, 0) >= %s')
        params.append(min_rec_td)
    if min_tackles is not None and min_tackles > 0:
        where_clauses.append('AND COALESCE(ls.season_tackles, 0) >= %s')
        params.append(min_tackles)
    if min_sacks is not None and min_sacks > 0:
        where_clauses.append('AND COALESCE(ls.season_defensive_sacks, 0) >= %s')
        params.append(min_sacks)
    if min_int is not None and min_int > 0:
        where_clauses.append('AND COALESCE(ls.season_defensive_interceptions, 0) >= %s')
        params.append(min_int)
    if min_tfl is not None and min_tfl > 0:
        where_clauses.append('AND COALESCE(ls.season_tackles_for_loss, 0) >= %s')
        params.append(min_tfl)

    query = f"""
        WITH latest_stats AS (
            {stats_cte}
        ),
        latest_team AS (
            SELECT DISTINCT ON (pf.player_name)
                pf.player_name, t.name AS team_name, t.team_id
            FROM playsfor pf
            JOIN team t ON t.team_id = pf.team_id
            ORDER BY pf.player_name, pf.season DESC NULLS LAST
        ),
        canonical_player AS (
            SELECT DISTINCT ON (p.name)
                p.name, p.number, p.position, p.height, p.war
            FROM player p
            LEFT JOIN playsfor pf ON pf.player_name = p.name AND pf.player_number = p.number
            ORDER BY p.name, pf.season DESC NULLS LAST
        )
        SELECT
            p.name       AS player_name,
            p.number     AS player_number,
            p.position,
            p.height,
            ls.season,
            COALESCE(lt.team_name, 'Unknown')                        AS team_name,
            lt.team_id,
            COALESCE(ls.season_rushing_yards, 0)                     AS season_rushing_yards,
            COALESCE(ls.season_rushing_attempts, 0)                  AS season_rushing_attempts,
            COALESCE(ls.season_rushing_touchdowns, 0)                AS season_rushing_touchdowns,
            COALESCE(ls.season_passing_yards, 0)                     AS season_passing_yards,
            COALESCE(ls.season_passing_attempts, 0)                  AS season_passing_attempts,
            COALESCE(ls.season_passing_completions, 0)               AS season_passing_completions,
            COALESCE(ls.season_passing_touchdowns, 0)                AS season_passing_touchdowns,
            COALESCE(ls.season_receiving_yards, 0)                   AS season_receiving_yards,
            COALESCE(ls.season_receiving_attempts, 0)                AS season_receiving_attempts,
            COALESCE(ls.season_receiving_touchdowns, 0)              AS season_receiving_touchdowns,
            COALESCE(ls.season_tackles, 0)                           AS season_tackles,
            COALESCE(ls.season_defensive_sacks, 0)                   AS season_defensive_sacks,
            COALESCE(ls.season_defensive_interceptions, 0)           AS season_defensive_interceptions,
            COALESCE(ls.season_tackles_for_loss, 0)                  AS season_tackles_for_loss,
            COALESCE(ls.season_forced_fumbles, 0)                    AS season_forced_fumbles,
            COALESCE(ls.season_fumble_recoveries, 0)                 AS season_fumble_recoveries,
            COALESCE(ls.season_special_teams_returns, 0)             AS season_special_teams_returns,
            COALESCE(ls.season_special_teams_yards, 0)               AS season_special_teams_yards,
            COALESCE(ls.season_special_teams_touchdowns, 0)          AS season_special_teams_touchdowns,
            COALESCE(ls.season_punting_yards, 0)                     AS season_punting_yards,
            COALESCE(ls.season_punting_attempts, 0)                  AS season_punting_attempts,
            COALESCE(ls.season_kicking_attempts, 0)                  AS season_kicking_attempts,
            COALESCE(ls.season_kicking_made, 0)                      AS season_kicking_made,
            COALESCE(ls.season_extra_point_attempts, 0)              AS season_extra_point_attempts,
            COALESCE(ls.season_extra_points_made, 0)                 AS season_extra_points_made,
            COALESCE(ls.season_war, 0)                               AS season_war
        FROM canonical_player p
        LEFT JOIN latest_stats ls ON ls.player_name = p.name
        LEFT JOIN latest_team lt  ON lt.player_name = p.name
        WHERE 1=1
        {season_join_filter}
        {pos_filter}
        {name_filter}
        {chr(10).join(where_clauses)}
        ORDER BY {order_by} {order.upper()} NULLS LAST
    """

    rows = run_all(query, params=tuple(params) if params else None)

    teams = run_all("SELECT team_id, name FROM team ORDER BY name")

    any_filter_active = bool(
        season or team_id or min_height or
        min_rush or min_pass or min_rec or
        min_rush_td or min_pass_td or min_rec_td or
        min_tackles or min_sacks or min_int or min_tfl
    )

    return render_template('players/players.html',
        players=rows,
        current_group=group,
        current_sort=sort,
        current_order=order,
        search_query=search_query,
        current_season=season,
        team_id=team_id,
        min_height=min_height,
        min_rush=min_rush,
        min_pass=min_pass,
        min_rec=min_rec,
        min_rush_td=min_rush_td,
        min_pass_td=min_pass_td,
        min_rec_td=min_rec_td,
        min_tackles=min_tackles,
        min_sacks=min_sacks,
        min_int=min_int,
        min_tfl=min_tfl,
        any_filter_active=any_filter_active,
        available_seasons=[2026, 2025, 2024, 2023],
        teams=teams,
    )


@players_bp.route('/players/<path:name>/<int:number>')
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
            season_tackles_for_loss, season_forced_fumbles, season_fumble_recoveries,
            season_offensive_interceptions,
            season_war
        FROM season_stats
        WHERE player_name = %s AND player_number = %s
        ORDER BY season DESC
    """, params=(name, number))

    career_stats = run_one("""
        SELECT
            COUNT(DISTINCT season)                           AS seasons,
            COALESCE(SUM(season_rushing_yards), 0)           AS career_rushing_yards,
            COALESCE(SUM(season_passing_yards), 0)           AS career_passing_yards,
            COALESCE(SUM(season_receiving_yards), 0)         AS career_receiving_yards,
            COALESCE(SUM(season_rushing_touchdowns), 0)      AS career_rushing_touchdowns,
            COALESCE(SUM(season_passing_touchdowns), 0)      AS career_passing_touchdowns,
            COALESCE(SUM(season_receiving_touchdowns), 0)    AS career_receiving_touchdowns,
            COALESCE(SUM(season_tackles), 0)                 AS career_tackles,
            COALESCE(SUM(season_defensive_sacks), 0)         AS career_sacks,
            COALESCE(SUM(season_defensive_interceptions), 0) AS career_interceptions,
            COALESCE(SUM(season_tackles_for_loss), 0)        AS career_tfl,
            COALESCE(SUM(season_forced_fumbles), 0)          AS career_forced_fumbles,
            COALESCE(SUM(season_fumble_recoveries), 0)       AS career_fumble_recoveries,
            ROUND(SUM(season_war)::NUMERIC, 2)               AS career_war
        FROM season_stats
        WHERE player_name = %s AND player_number = %s
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
        career_stats=career_stats or {},
        teams=teams,
        career_view=False,
    )
