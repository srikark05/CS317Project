from flask import Blueprint, render_template, request, redirect, url_for
from app import run_all, run_one
import json
import os

players_bp = Blueprint('players', __name__)

OFFENSE_POSITIONS = ('QB', 'RB', 'WR', 'TE', 'OL', 'OT', 'OG', 'OC', 'FB')
DEFENSE_POSITIONS = ('DL', 'DE', 'DT', 'LB', 'CB', 'SS', 'FS', 'DB', 'NT')
SPECIAL_POSITIONS = ('K', 'P', 'LS', 'KR', 'PR')

config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
with open(config_path) as f:
    config = json.load(f)

POINTS_PER_WIN = config['points_per_win']
WAR_WEIGHTS = {
    'season_rushing_yards': config['stat_weights'].get('rushing_yards', 0),
    'season_receiving_yards': config['stat_weights'].get('receiving_yards', 0),
    'season_passing_yards': config['stat_weights'].get('passing_yards', 0),
    'season_rushing_touchdowns': config['stat_weights'].get('touchdowns', 0),
    'season_passing_touchdowns': config['stat_weights'].get('touchdowns', 0),
    'season_receiving_touchdowns': config['stat_weights'].get('touchdowns', 0),
    'season_tackles': config['stat_weights'].get('tackles', 0),
    'season_defensive_sacks': config['stat_weights'].get('sacks', 0),
    'season_defensive_interceptions': config['stat_weights'].get('interceptions', 0),
    'season_tackles_for_loss': config['stat_weights'].get('tackles_for_loss', 0),
    'season_forced_fumbles': config['stat_weights'].get('fumbles', 0),
    'season_fumble_recoveries': 0,
    'season_offensive_interceptions': config['stat_weights'].get('interceptions', 0),
}

def calculate_replacement_levels_by_position(season):
    rows = run_all("""
        SELECT p.position,
               AVG(ss.season_rushing_yards) as avg_rushing_yards,
               AVG(ss.season_receiving_yards) as avg_receiving_yards,
               AVG(ss.season_passing_yards) as avg_passing_yards,
               AVG(ss.season_rushing_touchdowns) as avg_rushing_touchdowns,
               AVG(ss.season_passing_touchdowns) as avg_passing_touchdowns,
               AVG(ss.season_receiving_touchdowns) as avg_receiving_touchdowns,
               AVG(ss.season_tackles) as avg_tackles,
               AVG(ss.season_defensive_sacks) as avg_defensive_sacks,
               AVG(ss.season_defensive_interceptions) as avg_defensive_interceptions,
               AVG(ss.season_tackles_for_loss) as avg_tackles_for_loss,
               AVG(ss.season_forced_fumbles) as avg_forced_fumbles,
               AVG(ss.season_fumble_recoveries) as avg_fumble_recoveries,
               AVG(ss.season_offensive_interceptions) as avg_offensive_interceptions
        FROM season_stats ss
        JOIN player p ON p.name = ss.player_name AND p.number = ss.player_number
        WHERE ss.season = %s
        GROUP BY p.position
    """, params=(season,))
    replacement = {}
    for row in rows:
        pos = row['position']
        replacement[pos] = {
            'season_rushing_yards': row['avg_rushing_yards'] or 0,
            'season_receiving_yards': row['avg_receiving_yards'] or 0,
            'season_passing_yards': row['avg_passing_yards'] or 0,
            'season_rushing_touchdowns': row['avg_rushing_touchdowns'] or 0,
            'season_passing_touchdowns': row['avg_passing_touchdowns'] or 0,
            'season_receiving_touchdowns': row['avg_receiving_touchdowns'] or 0,
            'season_tackles': row['avg_tackles'] or 0,
            'season_defensive_sacks': row['avg_defensive_sacks'] or 0,
            'season_defensive_interceptions': row['avg_defensive_interceptions'] or 0,
            'season_tackles_for_loss': row['avg_tackles_for_loss'] or 0,
            'season_forced_fumbles': row['avg_forced_fumbles'] or 0,
            'season_fumble_recoveries': row['avg_fumble_recoveries'] or 0,
            'season_offensive_interceptions': row['avg_offensive_interceptions'] or 0,
        }
    return replacement

def calculate_war(stats, replacement):
    total = 0.0
    for field, weight in WAR_WEIGHTS.items():
        player_val = float(stats.get(field) or 0)
        repl_val = float(replacement.get(field) or 0)
        total += (player_val - repl_val) * weight
    return round(total / POINTS_PER_WIN, 3)

def annotate_season_stats_rows(rows, position, replacement_by_season):
    for row in rows:
        season = row['season']
        repl = replacement_by_season.get(season, {}).get(position, {})
        row['season_war'] = calculate_war(row, repl)
    return rows


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

    if search_query:
        name_filter = "AND p.name ILIKE %s"
        params.append(f"%{search_query}%")
    else:
        name_filter = ""

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
            p.name       AS player_name,
            p.number     AS player_number,
            p.position,
            p.war,
            ls.season,
            COALESCE(lt.team_name, 'Unknown') AS team_name,
            COALESCE(ls.season_rushing_yards, 0)       AS season_rushing_yards,
            COALESCE(ls.season_passing_yards, 0)       AS season_passing_yards,
            COALESCE(ls.season_receiving_yards, 0)     AS season_receiving_yards,
            COALESCE(ls.season_rushing_touchdowns, 0)  AS season_rushing_touchdowns,
            COALESCE(ls.season_passing_touchdowns, 0)  AS season_passing_touchdowns,
            COALESCE(ls.season_tackles, 0)             AS season_tackles
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
            season_offensive_interceptions
        FROM season_stats
        WHERE player_name = %s AND player_number = %s
        ORDER BY season DESC
    """, params=(name, number))

    seasons = set(row['season'] for row in season_stats if row['season'])
    replacement_by_season = {s: calculate_replacement_levels_by_position(s) for s in seasons}
    season_stats = annotate_season_stats_rows(season_stats, player['position'], replacement_by_season)

    career_stats = run_one("""
        SELECT
            COUNT(DISTINCT season) AS seasons,
            COALESCE(SUM(season_rushing_yards), 0)        AS career_rushing_yards,
            COALESCE(SUM(season_passing_yards), 0)        AS career_passing_yards,
            COALESCE(SUM(season_receiving_yards), 0)      AS career_receiving_yards,
            COALESCE(SUM(season_rushing_touchdowns), 0)   AS career_rushing_touchdowns,
            COALESCE(SUM(season_passing_touchdowns), 0)   AS career_passing_touchdowns,
            COALESCE(SUM(season_receiving_touchdowns), 0) AS career_receiving_touchdowns,
            COALESCE(SUM(season_tackles), 0)              AS career_tackles,
            COALESCE(SUM(season_defensive_sacks), 0)      AS career_sacks,
            COALESCE(SUM(season_defensive_interceptions), 0) AS career_interceptions,
            COALESCE(SUM(season_tackles_for_loss), 0)     AS career_tfl,
            COALESCE(SUM(season_forced_fumbles), 0)       AS career_forced_fumbles,
            COALESCE(SUM(season_fumble_recoveries), 0)    AS career_fumble_recoveries,
            COALESCE(SUM(season_offensive_interceptions), 0) AS career_offensive_interceptions
        FROM season_stats
        WHERE player_name = %s AND player_number = %s
    """, params=(name, number))

    career_stats = career_stats or {}
    career_stats['career_war'] = round(sum(r.get('season_war', 0) for r in season_stats), 3)

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
        career_stats=career_stats,
        teams=teams,
        career_view=False
    )


@players_bp.route('/players/<path:name>/<int:number>/career')
def career(name, number):
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
            season_offensive_interceptions
        FROM season_stats
        WHERE player_name = %s AND player_number = %s
        ORDER BY season DESC
    """, params=(name, number))

    seasons = set(row['season'] for row in season_stats if row['season'])
    replacement_by_season = {s: calculate_replacement_levels_by_position(s) for s in seasons}
    season_stats = annotate_season_stats_rows(season_stats, player['position'], replacement_by_season)

    career_stats = run_one("""
        SELECT
            COUNT(DISTINCT season) AS seasons,
            COALESCE(SUM(season_rushing_yards), 0)        AS career_rushing_yards,
            COALESCE(SUM(season_passing_yards), 0)        AS career_passing_yards,
            COALESCE(SUM(season_receiving_yards), 0)      AS career_receiving_yards,
            COALESCE(SUM(season_rushing_touchdowns), 0)   AS career_rushing_touchdowns,
            COALESCE(SUM(season_passing_touchdowns), 0)   AS career_passing_touchdowns,
            COALESCE(SUM(season_receiving_touchdowns), 0) AS career_receiving_touchdowns,
            COALESCE(SUM(season_tackles), 0)              AS career_tackles,
            COALESCE(SUM(season_defensive_sacks), 0)      AS career_sacks,
            COALESCE(SUM(season_defensive_interceptions), 0) AS career_interceptions,
            COALESCE(SUM(season_tackles_for_loss), 0)     AS career_tfl,
            COALESCE(SUM(season_forced_fumbles), 0)       AS career_forced_fumbles,
            COALESCE(SUM(season_fumble_recoveries), 0)    AS career_fumble_recoveries,
            COALESCE(SUM(season_offensive_interceptions), 0) AS career_offensive_interceptions
        FROM season_stats
        WHERE player_name = %s AND player_number = %s
    """, params=(name, number))

    career_stats = career_stats or {}
    career_stats['career_war'] = round(sum(r.get('season_war', 0) for r in season_stats), 3)

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
        career_stats=career_stats,
        teams=teams,
        career_view=True
    )
