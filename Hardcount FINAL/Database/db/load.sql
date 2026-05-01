-- ============================================================
-- WNFC Database - load.sql (PostgreSQL)
-- ============================================================

DROP TABLE IF EXISTS staging_wnfc_player_stats;

CREATE TABLE staging_wnfc_player_stats (
    player_name               VARCHAR(100),
    player_number             DECIMAL(8,2),
    position                  VARCHAR(10),
    height                    VARCHAR(20),
    weight                    DECIMAL(8,2),
    birth_year                DECIMAL(8,2),
    hometown                  VARCHAR(100),
    home_state                VARCHAR(50),
    school                    VARCHAR(200),
    passing_yards             DECIMAL(10,2),
    passing_comp              DECIMAL(10,2),
    passing_att               DECIMAL(10,2),
    passing_pct               DECIMAL(10,2),
    passing_td                DECIMAL(10,2),
    passing_int               DECIMAL(10,2),
    passing_long              DECIMAL(10,2),
    passing_rating            DECIMAL(10,2),
    rushing_yards             DECIMAL(10,2),
    rushing_carries           DECIMAL(10,2),
    rushing_long              DECIMAL(10,2),
    rushing_td                DECIMAL(10,2),
    receiving_yards           DECIMAL(10,2),
    receiving_rec             DECIMAL(10,2),
    receiving_long            DECIMAL(10,2),
    receiving_td              DECIMAL(10,2),
    tackles_solo              DECIMAL(10,2),
    tackles_assists           DECIMAL(10,2),
    tackles_for_loss          DECIMAL(10,2),
    sacks                     DECIMAL(10,2),
    forced_fumbles            DECIMAL(10,2),
    interceptions             DECIMAL(10,2),
    interception_return_yards DECIMAL(10,2),
    interception_return_long  DECIMAL(10,2),
    interception_return_td    DECIMAL(10,2),
    fumble_recoveries         DECIMAL(10,2),
    fumble_return_yards       VARCHAR(20),
    fumble_return_long        VARCHAR(20),
    fumble_return_td          DECIMAL(10,2),
    pass_deflections          DECIMAL(10,2),
    blocked_kicks_and_punts   DECIMAL(10,2),
    kickoff_returns           DECIMAL(10,2),
    kickoff_returns_yards     DECIMAL(10,2),
    kickoff_returns_long      DECIMAL(10,2),
    kickoff_returns_td        DECIMAL(10,2),
    punt_returns              DECIMAL(10,2),
    punt_return_yards         DECIMAL(10,2),
    punt_return_long          DECIMAL(10,2),
    punt_return_td            DECIMAL(10,2),
    punts                     DECIMAL(10,2),
    punting_yards             DECIMAL(10,2),
    punting_touchbacks        DECIMAL(10,2),
    punting_long              DECIMAL(10,2),
    touchdowns                DECIMAL(10,2),
    field_goals               DECIMAL(10,2),
    field_goal_att            DECIMAL(10,2),
    field_goal_long           DECIMAL(10,2),
    pat_kicks                 DECIMAL(10,2),
    pat_kicks_att             DECIMAL(10,2),
    safeties                  DECIMAL(10,2),
    pat_conversions           DECIMAL(10,2),
    season                    DECIMAL(10,2),
    team                      VARCHAR(100),
    nr                        VARCHAR(20)
);

\copy staging_wnfc_player_stats (player_name, player_number, position, height, weight, birth_year, hometown, home_state, school, passing_yards, passing_comp, passing_att, passing_pct, passing_td, passing_int, passing_long, passing_rating, rushing_yards, rushing_carries, rushing_long, rushing_td, receiving_yards, receiving_rec, receiving_long, receiving_td, tackles_solo, tackles_assists, tackles_for_loss, sacks, forced_fumbles, interceptions, interception_return_yards, interception_return_long, interception_return_td, fumble_recoveries, fumble_return_yards, fumble_return_long, fumble_return_td, pass_deflections, blocked_kicks_and_punts, kickoff_returns, kickoff_returns_yards, kickoff_returns_long, kickoff_returns_td, punt_returns, punt_return_yards, punt_return_long, punt_return_td, punts, punting_yards, punting_touchbacks, punting_long, touchdowns, field_goals, field_goal_att, field_goal_long, pat_kicks, pat_kicks_att, safeties, pat_conversions, season, team, nr) FROM '/tmp/master_clean_fixed.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"');

-- ============================================================
-- Positions
-- ============================================================
INSERT INTO Positions (position)
SELECT DISTINCT LEFT(TRIM(position), 2)
FROM staging_wnfc_player_stats
WHERE position IS NOT NULL AND TRIM(position) <> ''
ON CONFLICT DO NOTHING;

-- ============================================================
-- Players
-- ============================================================
INSERT INTO Player (name, dob, position, number, weight, height, war)
SELECT DISTINCT ON (s.player_name, s.player_number)
    s.player_name,
    TO_DATE(s.birth_year::TEXT || '-01-01', 'YYYY-MM-DD') AS dob,
    LEFT(TRIM(s.position), 2) AS position,
    s.player_number,
    s.weight,
    CASE
        WHEN s.height ~ '^\d+-\d+$'
            THEN (SPLIT_PART(s.height, '-', 1)::INT * 12)
               + SPLIT_PART(s.height, '-', 2)::INT
        ELSE NULL
    END AS height,
    NULL::FLOAT AS war
FROM staging_wnfc_player_stats s
WHERE s.player_name IS NOT NULL AND s.player_number IS NOT NULL
ON CONFLICT DO NOTHING;

-- ============================================================
-- Teams
-- ============================================================
INSERT INTO Team (name)
SELECT DISTINCT TRIM(s.team)
FROM staging_wnfc_player_stats s
WHERE s.team IS NOT NULL AND TRIM(s.team) <> ''
ON CONFLICT DO NOTHING;

-- ============================================================
-- PlaysFor
-- ============================================================
-- Disable duplicate jersey trigger during bulk load (data has known jersey overlaps)
ALTER TABLE PlaysFor DISABLE TRIGGER no_dupe_player;

INSERT INTO PlaysFor (player_id, player_name, player_number, team_id, season)
SELECT DISTINCT
    p.player_id,
    s.player_name,
    s.player_number,
    t.team_id,
    s.season
FROM staging_wnfc_player_stats s
JOIN Team t ON t.name = TRIM(s.team)
JOIN Player p ON p.name = s.player_name AND p.number = s.player_number
WHERE s.player_name IS NOT NULL AND s.player_number IS NOT NULL AND s.season IS NOT NULL
ON CONFLICT DO NOTHING;

ALTER TABLE PlaysFor ENABLE TRIGGER no_dupe_player;

-- ============================================================
-- Season Stats
-- ============================================================
INSERT INTO season_stats (
    player_id, player_name, player_number, season,
    season_rushing_yards, season_rushing_attempts, season_rushing_touchdowns,
    season_receiving_yards, season_receiving_attempts, season_receiving_touchdowns,
    season_passing_yards, season_passing_attempts, season_passing_completions, season_passing_touchdowns,
    season_offensive_interceptions, season_defensive_interceptions,
    season_offensive_sacks, season_defensive_sacks,
    season_tackles, season_tackles_for_loss,
    season_fumbles, season_forced_fumbles, season_fumble_recoveries,
    season_special_teams_returns, season_special_teams_touchdowns, season_special_teams_yards,
    season_punting_yards, season_punting_attempts,
    season_kicking_attempts, season_kicking_made,
    season_extra_point_attempts, season_extra_points_made
)
SELECT
    p.player_id,
    s.player_name,
    s.player_number,
    s.season,
    COALESCE(s.rushing_yards, 0),
    COALESCE(s.rushing_carries, 0),
    COALESCE(s.rushing_td, 0),
    COALESCE(s.receiving_yards, 0),
    COALESCE(s.receiving_rec, 0),
    COALESCE(s.receiving_td, 0),
    COALESCE(s.passing_yards, 0),
    COALESCE(s.passing_att, 0),
    COALESCE(s.passing_comp, 0),
    COALESCE(s.passing_td, 0),
    COALESCE(s.passing_int, 0),
    COALESCE(s.interceptions, 0),
    0,
    COALESCE(s.sacks, 0),
    COALESCE(s.tackles_solo, 0) + COALESCE(s.tackles_assists, 0),
    COALESCE(s.tackles_for_loss, 0),
    0,
    COALESCE(s.forced_fumbles, 0),
    COALESCE(s.fumble_recoveries, 0),
    COALESCE(s.kickoff_returns, 0) + COALESCE(s.punt_returns, 0),
    COALESCE(s.kickoff_returns_td, 0) + COALESCE(s.punt_return_td, 0),
    COALESCE(s.kickoff_returns_yards, 0) + COALESCE(s.punt_return_yards, 0),
    COALESCE(s.punting_yards, 0),
    COALESCE(s.punts, 0),
    COALESCE(s.field_goal_att, 0),
    COALESCE(s.field_goals, 0),
    COALESCE(s.pat_kicks_att, 0),
    COALESCE(s.pat_kicks, 0)
FROM staging_wnfc_player_stats s
WHERE s.player_name IS NOT NULL AND s.player_number IS NOT NULL AND s.season IS NOT NULL
ON CONFLICT DO NOTHING;