-- ============================================================
-- WNFC Database - loadgames.sql (PostgreSQL)
-- Run AFTER loadteams.sql (requires staging_wnfc_teams to exist)
-- ============================================================

DROP TABLE IF EXISTS staging_wnfc_games;

CREATE TABLE staging_wnfc_games (
    week_number         VARCHAR(5),   -- VARCHAR to handle P1, P2, P3 playoff weeks
    month               INT,
    day_approx          INT,          -- CSV header is day_(approx), mapped by position below
    home_team_index     INT,
    away_team_index     INT,
    home_team_score     INT,
    away_team_score     INT,
    winning_team_index  INT,
    season              INT
);

-- Column list used so the parentheses in CSV header "day_(approx)" don't cause issues
\copy staging_wnfc_games (week_number, month, day_approx, home_team_index, away_team_index, home_team_score, away_team_score, winning_team_index, season) FROM '/tmp/wnfc_games_master.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"');

-- ============================================================
-- Games
-- ============================================================
-- Playoff weeks P1/P2/P3 are mapped to week numbers 9/10/11.
-- Team index is resolved to team_id via staging_wnfc_teams → Team.
-- ============================================================
INSERT INTO Games (week, season, play_date, date_time, score, home_team, away_team)
SELECT
    CASE
        WHEN g.week_number ~ '^\d+$' THEN g.week_number::INT
        WHEN g.week_number = 'P1'    THEN 9
        WHEN g.week_number = 'P2'    THEN 10
        WHEN g.week_number = 'P3'    THEN 11
        ELSE 99
    END AS week,
    g.season,
    TO_DATE(
        g.season::TEXT || '-' || LPAD(g.month::TEXT, 2, '0') || '-' || LPAD(g.day_approx::TEXT, 2, '0'),
        'YYYY-MM-DD'
    ) AS play_date,
    TO_TIMESTAMP(
        g.season::TEXT || '-' || LPAD(g.month::TEXT, 2, '0') || '-' || LPAD(g.day_approx::TEXT, 2, '0'),
        'YYYY-MM-DD'
    ) AS date_time,
    g.home_team_score::TEXT || '-' || g.away_team_score::TEXT AS score,
    ht.team_id  AS home_team,
    at_.team_id AS away_team
FROM staging_wnfc_games g
JOIN staging_wnfc_teams  st_h  ON st_h.team_index  = g.home_team_index AND st_h.season  = g.season
JOIN Team                ht    ON ht.name           = TRIM(st_h.team_name)
JOIN staging_wnfc_teams  st_a  ON st_a.team_index   = g.away_team_index AND st_a.season  = g.season
JOIN Team                at_   ON at_.name          = TRIM(st_a.team_name)
ON CONFLICT DO NOTHING;
