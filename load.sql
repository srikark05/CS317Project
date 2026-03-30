

START TRANSACTION;

DROP TABLE IF EXISTS staging_wnfc_player_stats;

CREATE TABLE staging_wnfc_player_stats (
    player_name VARCHAR(100),
    player_number INT,
    position VARCHAR(10),
    height VARCHAR(20),
    weight INT,
    birth_year INT,
    hometown VARCHAR(100),
    home_state VARCHAR(50),
    school VARCHAR(200),
    passing_yards INT,
    passing_comp INT,
    passing_att INT,
    passing_pct DECIMAL(6,2),
    passing_td INT,
    passing_int INT,
    passing_long INT,
    passing_rating DECIMAL(8,2),
    rushing_yards INT,
    rushing_carries INT,
    rushing_long INT,
    rushing_td INT,
    receiving_yards INT,
    receiving_rec INT,
    receiving_long INT,
    receiving_td INT,
    tackles_solo DECIMAL(8,2),
    tackles_assists DECIMAL(8,2),
    tackles_for_loss DECIMAL(8,2),
    sacks DECIMAL(8,2),
    forced_fumbles INT,
    interceptions INT,
    interception_return_yards INT,
    interception_return_long INT,
    interception_return_td INT,
    fumble_recoveries INT,
    fumble_return_yards VARCHAR(20),
    fumble_return_long VARCHAR(20),
    fumble_return_td INT,
    pass_deflections INT,
    blocked_kicks_and_punts INT,
    kickoff_returns INT,
    kickoff_returns_yards INT,
    kickoff_returns_long INT,
    kickoff_returns_td INT,
    punt_returns INT,
    punt_return_yards INT,
    punt_return_long INT,
    punt_return_td INT,
    punts INT,
    punting_yards INT,
    punting_touchbacks INT,
    punting_long INT,
    touchdowns INT,
    field_goals INT,
    field_goal_att INT,
    field_goal_long INT,
    pat_kicks INT,
    pat_kicks_att INT,
    safeties INT,
    pat_conversions INT,
    season INT,
    team VARCHAR(100)
);

LOAD DATA LOCAL INFILE '../Data/wnfc_player_stats_master.csv'
INTO TABLE staging_wnfc_player_stats
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    player_name, player_number, position, height, weight, birth_year, hometown, home_state, school,
    passing_yards, passing_comp, passing_att, passing_pct, passing_td, passing_int, passing_long, passing_rating,
    rushing_yards, rushing_carries, rushing_long, rushing_td,
    receiving_yards, receiving_rec, receiving_long, receiving_td,
    tackles_solo, tackles_assists, tackles_for_loss, sacks,
    forced_fumbles, interceptions, interception_return_yards, interception_return_long, interception_return_td,
    fumble_recoveries, fumble_return_yards, fumble_return_long, fumble_return_td,
    pass_deflections, blocked_kicks_and_punts,
    kickoff_returns, kickoff_returns_yards, kickoff_returns_long, kickoff_returns_td,
    punt_returns, punt_return_yards, punt_return_long, punt_return_td,
    punts, punting_yards, punting_touchbacks, punting_long,
    touchdowns, field_goals, field_goal_att, field_goal_long,
    pat_kicks, pat_kicks_att, safeties, pat_conversions,
    season, team
);


INSERT IGNORE INTO Positions (position)
SELECT DISTINCT LEFT(TRIM(position), 2)
FROM staging_wnfc_player_stats
WHERE position IS NOT NULL AND TRIM(position) <> '';

INSERT IGNORE INTO Player (name, dob, position, number, weight, height, war)
SELECT
    s.player_name,
    STR_TO_DATE(CONCAT(s.birth_year, '-01-01'), '%Y-%m-%d') AS dob,
    LEFT(TRIM(s.position), 2) AS position,
    s.player_number,
    s.weight,
    CASE
        WHEN s.height REGEXP '^[0-9]+-[0-9]+$'
            THEN (CAST(SUBSTRING_INDEX(s.height, '-', 1) AS UNSIGNED) * 12)
               + CAST(SUBSTRING_INDEX(s.height, '-', -1) AS UNSIGNED)
        ELSE NULL
    END AS height,
    NULL AS war
FROM staging_wnfc_player_stats s
WHERE s.player_name IS NOT NULL;


INSERT IGNORE INTO Team (name)
SELECT DISTINCT TRIM(s.team)
FROM staging_wnfc_player_stats s
WHERE s.team IS NOT NULL AND TRIM(s.team) <> '';


INSERT IGNORE INTO PlaysFor (player_name, player_number, team_id, season)
SELECT DISTINCT
    s.player_name,
    s.player_number,
    t.Team_id,
    s.season
FROM staging_wnfc_player_stats s
JOIN Team t
    ON t.name = s.team;

INSERT IGNORE INTO season_stats (
    player_name, player_number, season,
    season_rushing_yards, season_rushing_attempts, season_rushing_touchdowns,
    season_receiving_yards, season_receiving_attempts, season_receiving_touchdowns,
    season_passing_yards, season_passing_attempts, season_passing_completions, season_passing_touchdowns,
    season_offensive_interceptions, season_defensive_interceptions,
    season_offensive_sacks, season_defensive_sacks,
    season_tackles, season_tackles_for_loss,
    season_forced_fumbles, season_fumble_recoveries,
    season_special_teams_returns, season_special_teams_touchdowns, season_special_teams_yards,
    season_punting_yards, season_punting_attempts,
    season_kicking_attempts, season_kicking_made,
    season_extra_point_attempts, season_extra_points_made
)
SELECT
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
FROM staging_wnfc_player_stats s;

COMMIT;
