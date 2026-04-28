from functools import wraps
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from app import run_all, run_one

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/admin')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')


@admin_bp.route('/admin/add-game', methods=['GET', 'POST'])
@admin_required
def add_game():
    teams = run_all("SELECT team_id, name FROM team ORDER BY name")
    coaches = run_all("SELECT name, dob FROM coach ORDER BY name")

    if request.method == 'POST':
        try:
            home_team_id  = int(request.form.get('home_team_id', '').strip())
            away_team_id  = int(request.form.get('away_team_id', '').strip())
            home_coach_name = request.form.get('home_coach_name', '').strip()
            home_coach_dob  = request.form.get('home_coach_dob', '').strip()
            away_coach_name = request.form.get('away_coach_name', '').strip()
            away_coach_dob  = request.form.get('away_coach_dob', '').strip()
            game_date = request.form.get('game_date', '').strip()
            week      = int(request.form.get('week', '').strip())
            season    = int(request.form.get('season', '').strip())
            score     = request.form.get('score', '').strip()
            address   = request.form.get('address', '').strip()

            if not all([home_team_id, away_team_id, home_coach_name, away_coach_name,
                        game_date, week, season]):
                flash('Missing required fields.', 'error')
                return render_template('admin/add_game.html', teams=teams, coaches=coaches)

            if home_team_id == away_team_id:
                flash('Home and away teams must be different.', 'error')
                return render_template('admin/add_game.html', teams=teams, coaches=coaches)

            # Ensure coaches exist
            for cn, cd in [(home_coach_name, home_coach_dob), (away_coach_name, away_coach_dob)]:
                run_all("""
                    INSERT INTO coach (name, dob)
                    SELECT %s, %s
                    WHERE NOT EXISTS (SELECT 1 FROM coach WHERE name = %s AND dob = %s)
                """, params=(cn, cd, cn, cd))

            # Link coaches to teams for this season
            for cn, cd, tid in [
                (home_coach_name, home_coach_dob, home_team_id),
                (away_coach_name, away_coach_dob, away_team_id),
            ]:
                run_all("""
                    INSERT INTO coachesfor (coach_name, coach_dob, team_id, season)
                    SELECT %s, %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM coachesfor
                        WHERE coach_name = %s AND coach_dob = %s
                          AND team_id = %s AND season = %s
                    )
                """, params=(cn, cd, tid, season, cn, cd, tid, season))

            # Insert game
            run_all("""
                INSERT INTO games (week, season, play_date, address, score, home_team, away_team)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, params=(week, season, game_date, address, score, home_team_id, away_team_id))

            # Process player stats (home then away)
            stat_fields = [
                'rushing_yards', 'rushing_attempts', 'rushing_touchdowns',
                'receiving_yards', 'receiving_attempts', 'receiving_touchdowns',
                'passing_yards', 'passing_attempts', 'passing_completions', 'passing_touchdowns',
                'offensive_interceptions', 'defensive_interceptions',
                'offensive_sacks', 'defensive_sacks',
                'tackles', 'tackles_for_loss', 'forced_fumbles', 'fumble_recoveries',
                'special_teams_returns', 'special_teams_touchdowns', 'special_teams_yards',
                'punting_yards', 'punting_attempts',
                'kicking_attempts', 'kicking_made',
                'extra_point_attempts', 'extra_points_made',
            ]

            for side in ('home', 'away'):
                team_id = home_team_id if side == 'home' else away_team_id
                for key in request.form:
                    if not key.startswith(f'{side}_player_') or not key.endswith('_name'):
                        continue
                    prefix = key[: -len('_name')]   # e.g. "home_player_0"
                    pname  = request.form.get(key, '').strip()
                    pnum   = request.form.get(f'{prefix}_number', '').strip()
                    if not pname or not pnum:
                        continue
                    pnum = int(pnum)

                    stats = {f: 0 for f in stat_fields}
                    for f in stat_fields:
                        val = request.form.get(f'{prefix}_{f}', '0').strip()
                        stats[f] = int(val) if val.isdigit() else 0

                    run_all("""
                        INSERT INTO played_in (
                            player_name, player_number, game_date, week, season, home_team,
                            game_rushing_yards, game_rushing_attempts, game_rushing_touchdowns,
                            game_receiving_yards, game_receiving_attempts, game_receiving_touchdowns,
                            game_passing_yards, game_passing_attempts, game_passing_completions,
                            game_passing_touchdowns, game_offensive_interceptions, game_defensive_interceptions,
                            game_offensive_sacks, game_defensive_sacks, game_tackles, game_tackles_for_loss,
                            game_forced_fumbles, game_fumble_recoveries, game_special_teams_returns,
                            game_special_teams_touchdowns, game_special_teams_yards, game_punting_yards,
                            game_punting_attempts, game_kicking_attempts, game_kicking_made,
                            game_extra_point_attempts, game_extra_points_made)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, params=(
                        pname, pnum, game_date, week, season, team_id,
                        stats['rushing_yards'], stats['rushing_attempts'], stats['rushing_touchdowns'],
                        stats['receiving_yards'], stats['receiving_attempts'], stats['receiving_touchdowns'],
                        stats['passing_yards'], stats['passing_attempts'], stats['passing_completions'],
                        stats['passing_touchdowns'], stats['offensive_interceptions'], stats['defensive_interceptions'],
                        stats['offensive_sacks'], stats['defensive_sacks'], stats['tackles'], stats['tackles_for_loss'],
                        stats['forced_fumbles'], stats['fumble_recoveries'], stats['special_teams_returns'],
                        stats['special_teams_touchdowns'], stats['special_teams_yards'], stats['punting_yards'],
                        stats['punting_attempts'], stats['kicking_attempts'], stats['kicking_made'],
                        stats['extra_point_attempts'], stats['extra_points_made'],
                    ))

                    run_all("""
                        INSERT INTO season_stats (
                            player_name, player_number, season,
                            season_rushing_yards, season_rushing_attempts, season_rushing_touchdowns,
                            season_receiving_yards, season_receiving_attempts, season_receiving_touchdowns,
                            season_passing_yards, season_passing_attempts, season_passing_completions,
                            season_passing_touchdowns, season_offensive_interceptions, season_defensive_interceptions,
                            season_offensive_sacks, season_defensive_sacks, season_tackles, season_tackles_for_loss,
                            season_forced_fumbles, season_fumble_recoveries, season_special_teams_returns,
                            season_special_teams_touchdowns, season_special_teams_yards, season_punting_yards,
                            season_punting_attempts, season_kicking_attempts, season_kicking_made,
                            season_extra_point_attempts, season_extra_points_made)
                        SELECT %s, %s, %s,
                            COALESCE(SUM(game_rushing_yards),0),
                            COALESCE(SUM(game_rushing_attempts),0),
                            COALESCE(SUM(game_rushing_touchdowns),0),
                            COALESCE(SUM(game_receiving_yards),0),
                            COALESCE(SUM(game_receiving_attempts),0),
                            COALESCE(SUM(game_receiving_touchdowns),0),
                            COALESCE(SUM(game_passing_yards),0),
                            COALESCE(SUM(game_passing_attempts),0),
                            COALESCE(SUM(game_passing_completions),0),
                            COALESCE(SUM(game_passing_touchdowns),0),
                            COALESCE(SUM(game_offensive_interceptions),0),
                            COALESCE(SUM(game_defensive_interceptions),0),
                            COALESCE(SUM(game_offensive_sacks),0),
                            COALESCE(SUM(game_defensive_sacks),0),
                            COALESCE(SUM(game_tackles),0),
                            COALESCE(SUM(game_tackles_for_loss),0),
                            COALESCE(SUM(game_forced_fumbles),0),
                            COALESCE(SUM(game_fumble_recoveries),0),
                            COALESCE(SUM(game_special_teams_returns),0),
                            COALESCE(SUM(game_special_teams_touchdowns),0),
                            COALESCE(SUM(game_special_teams_yards),0),
                            COALESCE(SUM(game_punting_yards),0),
                            COALESCE(SUM(game_punting_attempts),0),
                            COALESCE(SUM(game_kicking_attempts),0),
                            COALESCE(SUM(game_kicking_made),0),
                            COALESCE(SUM(game_extra_point_attempts),0),
                            COALESCE(SUM(game_extra_points_made),0)
                        FROM played_in
                        WHERE player_name = %s AND player_number = %s AND season = %s
                        ON CONFLICT (player_name, player_number, season) DO UPDATE SET
                            season_rushing_yards = EXCLUDED.season_rushing_yards,
                            season_rushing_attempts = EXCLUDED.season_rushing_attempts,
                            season_rushing_touchdowns = EXCLUDED.season_rushing_touchdowns,
                            season_receiving_yards = EXCLUDED.season_receiving_yards,
                            season_receiving_attempts = EXCLUDED.season_receiving_attempts,
                            season_receiving_touchdowns = EXCLUDED.season_receiving_touchdowns,
                            season_passing_yards = EXCLUDED.season_passing_yards,
                            season_passing_attempts = EXCLUDED.season_passing_attempts,
                            season_passing_completions = EXCLUDED.season_passing_completions,
                            season_passing_touchdowns = EXCLUDED.season_passing_touchdowns,
                            season_offensive_interceptions = EXCLUDED.season_offensive_interceptions,
                            season_defensive_interceptions = EXCLUDED.season_defensive_interceptions,
                            season_offensive_sacks = EXCLUDED.season_offensive_sacks,
                            season_defensive_sacks = EXCLUDED.season_defensive_sacks,
                            season_tackles = EXCLUDED.season_tackles,
                            season_tackles_for_loss = EXCLUDED.season_tackles_for_loss,
                            season_forced_fumbles = EXCLUDED.season_forced_fumbles,
                            season_fumble_recoveries = EXCLUDED.season_fumble_recoveries,
                            season_special_teams_returns = EXCLUDED.season_special_teams_returns,
                            season_special_teams_touchdowns = EXCLUDED.season_special_teams_touchdowns,
                            season_special_teams_yards = EXCLUDED.season_special_teams_yards,
                            season_punting_yards = EXCLUDED.season_punting_yards,
                            season_punting_attempts = EXCLUDED.season_punting_attempts,
                            season_kicking_attempts = EXCLUDED.season_kicking_attempts,
                            season_kicking_made = EXCLUDED.season_kicking_made,
                            season_extra_point_attempts = EXCLUDED.season_extra_point_attempts,
                            season_extra_points_made = EXCLUDED.season_extra_points_made
                    """, params=(pname, pnum, season, pname, pnum, season))

            flash('Game added successfully!', 'success')
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            flash(f'Error adding game: {e}', 'error')

    return render_template('admin/add_game.html', teams=teams, coaches=coaches)

@admin_bp.route('/admin/delete-game', methods=['GET', 'POST'])
@admin_required
def delete_game():
    if request.method == 'POST':
        try:
            game_date = request.form.get('game_date', '').strip()
            week = int(request.form.get('week', '').strip())
            season = int(request.form.get('season', '').strip())

            affected_players = run_all("""
                SELECT DISTINCT player_name, player_number
                FROM played_in
                WHERE game_date = %s AND week = %s AND season = %s
            """, params=(game_date, week, season))

            run_all("""
                DELETE FROM played_in
                WHERE game_date = %s AND week = %s AND season = %s
            """, params=(game_date, week, season))

            run_all("""
                DELETE FROM games
                WHERE play_date = %s AND week = %s AND season = %s
            """, params=(game_date, week, season))

            for p in affected_players:
                pname = p['player_name']
                pnum = p['player_number']

                run_all("""
                    DELETE FROM season_stats
                    WHERE player_name = %s
                      AND player_number = %s
                      AND season = %s
                      AND NOT EXISTS (
                          SELECT 1
                          FROM played_in
                          WHERE player_name = %s
                            AND player_number = %s
                            AND season = %s
                      )
                """, params=(pname, pnum, season, pname, pnum, season))

                run_all("""
                    INSERT INTO season_stats (
                        player_name, player_number, season,
                        season_rushing_yards, season_rushing_attempts, season_rushing_touchdowns,
                        season_receiving_yards, season_receiving_attempts, season_receiving_touchdowns,
                        season_passing_yards, season_passing_attempts, season_passing_completions,
                        season_passing_touchdowns, season_offensive_interceptions, season_defensive_interceptions,
                        season_offensive_sacks, season_defensive_sacks, season_tackles, season_tackles_for_loss,
                        season_forced_fumbles, season_fumble_recoveries, season_special_teams_returns,
                        season_special_teams_touchdowns, season_special_teams_yards, season_punting_yards,
                        season_punting_attempts, season_kicking_attempts, season_kicking_made,
                        season_extra_point_attempts, season_extra_points_made
                    )
                    SELECT %s, %s, %s,
                        COALESCE(SUM(game_rushing_yards),0),
                        COALESCE(SUM(game_rushing_attempts),0),
                        COALESCE(SUM(game_rushing_touchdowns),0),
                        COALESCE(SUM(game_receiving_yards),0),
                        COALESCE(SUM(game_receiving_attempts),0),
                        COALESCE(SUM(game_receiving_touchdowns),0),
                        COALESCE(SUM(game_passing_yards),0),
                        COALESCE(SUM(game_passing_attempts),0),
                        COALESCE(SUM(game_passing_completions),0),
                        COALESCE(SUM(game_passing_touchdowns),0),
                        COALESCE(SUM(game_offensive_interceptions),0),
                        COALESCE(SUM(game_defensive_interceptions),0),
                        COALESCE(SUM(game_offensive_sacks),0),
                        COALESCE(SUM(game_defensive_sacks),0),
                        COALESCE(SUM(game_tackles),0),
                        COALESCE(SUM(game_tackles_for_loss),0),
                        COALESCE(SUM(game_forced_fumbles),0),
                        COALESCE(SUM(game_fumble_recoveries),0),
                        COALESCE(SUM(game_special_teams_returns),0),
                        COALESCE(SUM(game_special_teams_touchdowns),0),
                        COALESCE(SUM(game_special_teams_yards),0),
                        COALESCE(SUM(game_punting_yards),0),
                        COALESCE(SUM(game_punting_attempts),0),
                        COALESCE(SUM(game_kicking_attempts),0),
                        COALESCE(SUM(game_kicking_made),0),
                        COALESCE(SUM(game_extra_point_attempts),0),
                        COALESCE(SUM(game_extra_points_made),0)
                    FROM played_in
                    WHERE player_name = %s AND player_number = %s AND season = %s
                    HAVING COUNT(*) > 0
                    ON CONFLICT (player_name, player_number, season) DO UPDATE SET
                        season_rushing_yards = EXCLUDED.season_rushing_yards,
                        season_rushing_attempts = EXCLUDED.season_rushing_attempts,
                        season_rushing_touchdowns = EXCLUDED.season_rushing_touchdowns,
                        season_receiving_yards = EXCLUDED.season_receiving_yards,
                        season_receiving_attempts = EXCLUDED.season_receiving_attempts,
                        season_receiving_touchdowns = EXCLUDED.season_receiving_touchdowns,
                        season_passing_yards = EXCLUDED.season_passing_yards,
                        season_passing_attempts = EXCLUDED.season_passing_attempts,
                        season_passing_completions = EXCLUDED.season_passing_completions,
                        season_passing_touchdowns = EXCLUDED.season_passing_touchdowns,
                        season_offensive_interceptions = EXCLUDED.season_offensive_interceptions,
                        season_defensive_interceptions = EXCLUDED.season_defensive_interceptions,
                        season_offensive_sacks = EXCLUDED.season_offensive_sacks,
                        season_defensive_sacks = EXCLUDED.season_defensive_sacks,
                        season_tackles = EXCLUDED.season_tackles,
                        season_tackles_for_loss = EXCLUDED.season_tackles_for_loss,
                        season_forced_fumbles = EXCLUDED.season_forced_fumbles,
                        season_fumble_recoveries = EXCLUDED.season_fumble_recoveries,
                        season_special_teams_returns = EXCLUDED.season_special_teams_returns,
                        season_special_teams_touchdowns = EXCLUDED.season_special_teams_touchdowns,
                        season_special_teams_yards = EXCLUDED.season_special_teams_yards,
                        season_punting_yards = EXCLUDED.season_punting_yards,
                        season_punting_attempts = EXCLUDED.season_punting_attempts,
                        season_kicking_attempts = EXCLUDED.season_kicking_attempts,
                        season_kicking_made = EXCLUDED.season_kicking_made,
                        season_extra_point_attempts = EXCLUDED.season_extra_point_attempts,
                        season_extra_points_made = EXCLUDED.season_extra_points_made
                """, params=(pname, pnum, season, pname, pnum, season))

            flash('Game deleted successfully!', 'success')
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            flash(f'Error deleting game: {e}', 'error')

    return render_template('admin/delete_games.html')