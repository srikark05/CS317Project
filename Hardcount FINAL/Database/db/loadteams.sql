-- ============================================================
-- WNFC Database - loadteams.sql (PostgreSQL)
-- Run this BEFORE loadgames.sql
-- ============================================================

DROP TABLE IF EXISTS staging_wnfc_teams;

CREATE TABLE staging_wnfc_teams (
    team_index                  INT,
    team_name                   VARCHAR(100),
    division                    VARCHAR(100),
    team_website                VARCHAR(500),
    home_field                  VARCHAR(200),
    home_field_city             VARCHAR(100),
    home_field_state            VARCHAR(10),
    phone_number                VARCHAR(50),
    team_email                  VARCHAR(300),
    head_coach                  VARCHAR(100),
    assistant_hc                VARCHAR(100),
    offensive_coordinator       VARCHAR(100),
    defensive_coordinator       VARCHAR(100),
    special_teams_coordinator   VARCHAR(100),
    general_manager             VARCHAR(100),
    assistant_general_manager   VARCHAR(100),
    director_of_operations      VARCHAR(100),
    owner                       VARCHAR(100),
    pct                         DECIMAL(6,3),
    pf                          INT,
    pa                          INT,
    home_wins                   INT,
    home_loss                   INT,
    home_ties                   INT,
    road_win                    INT,
    road_loss                   INT,
    road_tie                    INT,
    div_win                     INT,
    div_loss                    INT,
    div_tie                     INT,
    non_div_win                 INT,
    non_div_loss                INT,
    non_div_tie                 INT,
    streak                      INT,
    season                      INT
);

-- CSV header: team_index,team_name,division,team_website,home_field,home_field_city,
--             home_field_state,phone_number,team_email,head_coach,assistant_hc,
--             offensive_coordinator,defensive_coordinator,special_teams_coordinator,
--             general_manager,assistant_general_manager,director_of_operations,owner,
--             pct,pf,pa,home_wins,home_loss,home_ties,road_win,road_loss,road_tie,
--             div_win,div_loss,div_tie,non_div_win,non_div_loss,non_div_tie,streak,season
\copy staging_wnfc_teams (team_index, team_name, division, team_website, home_field, home_field_city, home_field_state, phone_number, team_email, head_coach, assistant_hc, offensive_coordinator, defensive_coordinator, special_teams_coordinator, general_manager, assistant_general_manager, director_of_operations, owner, pct, pf, pa, home_wins, home_loss, home_ties, road_win, road_loss, road_tie, div_win, div_loss, div_tie, non_div_win, non_div_loss, non_div_tie, streak, season) FROM '/tmp/wnfc_teams_master.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"');

-- ============================================================
-- Teams
-- ============================================================

-- Insert teams not already in the table (player stats load may have added name-only rows)
INSERT INTO Team (name, division)
SELECT DISTINCT TRIM(t.team_name), TRIM(t.division)
FROM staging_wnfc_teams t
WHERE NOT EXISTS (
    SELECT 1 FROM Team WHERE name = TRIM(t.team_name)
)
AND t.team_name IS NOT NULL AND TRIM(t.team_name) <> '';

-- Update existing teams with full details (most recent season wins)
UPDATE Team SET
    division = s.division,
    address  = s.address
FROM (
    SELECT DISTINCT ON (TRIM(team_name))
        TRIM(team_name) AS team_name,
        TRIM(division)  AS division,
        TRIM(home_field)
            || CASE WHEN TRIM(COALESCE(home_field_city,  '')) NOT IN ('', 'NR')
                    THEN ', ' || TRIM(home_field_city)  ELSE '' END
            || CASE WHEN TRIM(COALESCE(home_field_state, '')) NOT IN ('', 'NR')
                    THEN ', ' || TRIM(home_field_state) ELSE '' END
        AS address
    FROM staging_wnfc_teams
    WHERE team_name IS NOT NULL AND TRIM(team_name) <> ''
    ORDER BY TRIM(team_name), season DESC
) s
WHERE Team.name = s.team_name;
