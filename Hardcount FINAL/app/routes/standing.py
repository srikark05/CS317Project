from flask import Blueprint, render_template, request
from app import run_all

standings_bp = Blueprint('standings', __name__)

@standings_bp.route('/standings')
def index():
    season = request.args.get('season', None)

    # Default to most recent season if none provided
    if not season:
        latest = run_all("SELECT MAX(season) AS s FROM staging_wnfc_teams")
        season = latest[0]['s'] if latest else 2025

    rows = run_all("""
        SELECT
            t.team_id,
            st.team_name                                                   AS name,
            st.division,
            (st.home_wins + st.road_win)                                   AS wins,
            (st.home_loss + st.road_loss)                                  AS losses,
            (st.home_ties + st.road_tie)                                   AS ties,
            st.pct,
            st.pf,
            st.pa,
            COALESCE(st.pf, 0) - COALESCE(st.pa, 0)                        AS point_diff,
            st.home_wins || '-' || st.home_loss || '-' || st.home_ties     AS home_rec,
            st.road_win  || '-' || st.road_loss || '-' || st.road_tie      AS road_rec,
            st.div_win   || '-' || st.div_loss  || '-' || st.div_tie       AS div_rec,
            st.streak
        FROM staging_wnfc_teams st
        LEFT JOIN team t ON LOWER(TRIM(t.name)) = LOWER(TRIM(st.team_name))
        WHERE st.season = %s
        ORDER BY st.division ASC, st.pct DESC, wins DESC
    """, params=(season,))

    seasons = run_all("""
        SELECT DISTINCT season FROM staging_wnfc_teams ORDER BY season DESC
    """)

    # Group rows by division for the template
    divisions = {}
    for r in (rows or []):
        d = r['division'] or 'Unknown'
        divisions.setdefault(d, []).append(r)

    return render_template('standings/standings.html',
        divisions=divisions,
        seasons=seasons,
        current_season=int(season)
    )
