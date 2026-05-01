from flask import Blueprint, render_template, request
from app import run_all, run_one

trades_bp = Blueprint('trades', __name__)

@trades_bp.route('/trades')
def index():
    season = request.args.get('season', None)

    filters = []
    params = []

    if season:
        filters.append("EXTRACT(YEAR FROM t.trade_date) = %s")
        params.append(season)

    where = "WHERE " + " AND ".join(filters) if filters else ""

    rows = run_all(f"""
        SELECT
            t.trade_date,
            t.trade_time,
            t.team_from_players,
            t.team_to_players,
            t.team_to_cash,
            tf.name AS team_from_name,
            tt.name AS team_to_name
        FROM trade t
        JOIN team tf ON tf.team_id = t.team_from
        JOIN team tt ON tt.team_id = t.team_to
        {where}
        ORDER BY t.trade_date DESC
    """, params=params if params else None)

    seasons = run_all("""
        SELECT DISTINCT EXTRACT(YEAR FROM trade_date)::INT AS season
        FROM trade
        ORDER BY season DESC
    """)

    return render_template('trades/trades.html',
        trades=rows,
        seasons=seasons,
        current_season=season
    )

@trades_bp.route('/trades/<int:team_from>/<int:team_to>/<string:trade_date>')
def detail(team_from, team_to, trade_date):
    trade = run_one("""
        SELECT
            t.trade_date,
            t.trade_time,
            t.team_from_players,
            t.team_to_players,
            t.team_to_cash,
            tf.name AS team_from_name,
            tt.name AS team_to_name
        FROM trade t
        JOIN team tf ON tf.team_id = t.team_from
        JOIN team tt ON tt.team_id = t.team_to
        WHERE t.team_from = %s
        AND t.team_to = %s
        AND t.trade_date = %s
    """, params=(team_from, team_to, trade_date))

    return render_template('trades/detail.html', trade=trade)