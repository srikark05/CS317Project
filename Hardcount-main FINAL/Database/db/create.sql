-- ============================================================
-- WNFC Database - create.sql (PostgreSQL)
-- ============================================================

CREATE TABLE Team (
    team_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    division VARCHAR(100),
    address VARCHAR(100),
    titles INT,
    president VARCHAR(100),
    tv_tag VARCHAR(3)
);

CREATE TABLE Positions (
    position VARCHAR(2) PRIMARY KEY
);

CREATE TABLE Offense (
    position VARCHAR(2) PRIMARY KEY,
    FOREIGN KEY (position) REFERENCES Positions(position)
);

CREATE TABLE Defense (
    position VARCHAR(2) PRIMARY KEY,
    FOREIGN KEY (position) REFERENCES Positions(position)
);

CREATE TABLE Special_Teams (
    position VARCHAR(2) PRIMARY KEY,
    FOREIGN KEY (position) REFERENCES Positions(position)
);

CREATE TABLE Player (
    player_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    dob DATE,
    position VARCHAR(2),
    number INT,
    weight INT,
    height INT,
    war FLOAT,
    UNIQUE (name, number),
    FOREIGN KEY (position) REFERENCES Positions(position)
);

CREATE TABLE Coach (
    name VARCHAR(100),
    dob DATE,
    record VARCHAR(50),
    PRIMARY KEY (name, dob)
);

CREATE TABLE Staff (
    staff_id INT,
    team_id INT,
    PRIMARY KEY (staff_id, team_id),
    FOREIGN KEY (team_id) REFERENCES Team(team_id)
);

CREATE TABLE Games (
    week INT,
    season INT,
    play_date DATE,
    date_time TIMESTAMP,
    address VARCHAR(100),
    score VARCHAR(20),
    home_team INT,
    away_team INT,
    PRIMARY KEY (week, season, home_team),
    FOREIGN KEY (home_team) REFERENCES Team(team_id),
    FOREIGN KEY (away_team) REFERENCES Team(team_id)
);

CREATE TABLE Trade (
    team_from INT,
    team_to INT,
    trade_date DATE,
    trade_time TIMESTAMP,
    team_from_players VARCHAR(1000),
    team_to_players VARCHAR(1000),
    team_to_cash DECIMAL(12,2),
    PRIMARY KEY (team_from, team_to, trade_date, trade_time),
    FOREIGN KEY (team_from) REFERENCES Team(team_id),
    FOREIGN KEY (team_to) REFERENCES Team(team_id)
);

CREATE TABLE PlaysFor (
    player_id INT,
    player_name VARCHAR(100),
    player_number INT,
    team_id INT,
    season INT,
    PRIMARY KEY (player_id, team_id, season),
    FOREIGN KEY (player_id) REFERENCES Player(player_id),
    FOREIGN KEY (player_name, player_number) REFERENCES Player(name, number),
    FOREIGN KEY (team_id) REFERENCES Team(team_id)
);

CREATE TABLE CoachesFor (
    coach_name VARCHAR(100),
    coach_dob DATE,
    team_id INT,
    season INT,
    PRIMARY KEY (coach_name, coach_dob, team_id, season),
    FOREIGN KEY (coach_name, coach_dob) REFERENCES Coach(name, dob),
    FOREIGN KEY (team_id) REFERENCES Team(team_id)
);

CREATE TABLE season_stats (
    player_id INT,
    player_name VARCHAR(100),
    player_number INT,
    season INT,
    season_rushing_yards INT DEFAULT 0,
    season_rushing_attempts INT DEFAULT 0,
    season_rushing_touchdowns INT DEFAULT 0,
    season_receiving_yards INT DEFAULT 0,
    season_receiving_attempts INT DEFAULT 0,
    season_receiving_touchdowns INT DEFAULT 0,
    season_passing_yards INT DEFAULT 0,
    season_passing_attempts INT DEFAULT 0,
    season_passing_completions INT DEFAULT 0,
    season_passing_touchdowns INT DEFAULT 0,
    season_offensive_interceptions INT DEFAULT 0,
    season_defensive_interceptions INT DEFAULT 0,
    season_offensive_sacks INT DEFAULT 0,
    season_defensive_sacks INT DEFAULT 0,
    season_tackles INT DEFAULT 0,
    season_tackles_for_loss INT DEFAULT 0,
    season_fumbles INT DEFAULT 0,
    season_forced_fumbles INT DEFAULT 0,
    season_fumble_recoveries INT DEFAULT 0,
    season_special_teams_returns INT DEFAULT 0,
    season_special_teams_touchdowns INT DEFAULT 0,
    season_special_teams_yards INT DEFAULT 0,
    season_punting_yards INT DEFAULT 0,
    season_punting_attempts INT DEFAULT 0,
    season_kicking_attempts INT DEFAULT 0,
    season_kicking_made INT DEFAULT 0,
    season_extra_point_attempts INT DEFAULT 0,
    season_extra_points_made INT DEFAULT 0,
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES Player(player_id),
    FOREIGN KEY (player_name, player_number) REFERENCES Player(name, number)
);


CREATE TABLE Played_In (
    player_id INT,
    player_name VARCHAR(100),
    player_number INT,
    game_date DATE,
    week INT,
    season INT,
    home_team INT,
    game_rushing_yards INT DEFAULT 0,
    game_rushing_attempts INT DEFAULT 0,
    game_rushing_touchdowns INT DEFAULT 0,
    game_receiving_yards INT DEFAULT 0,
    game_receiving_attempts INT DEFAULT 0,
    game_receiving_touchdowns INT DEFAULT 0,
    game_passing_yards INT DEFAULT 0,
    game_passing_attempts INT DEFAULT 0,
    game_passing_completions INT DEFAULT 0,
    game_passing_touchdowns INT DEFAULT 0,
    game_offensive_interceptions INT DEFAULT 0,
    game_defensive_interceptions INT DEFAULT 0,
    game_offensive_sacks INT DEFAULT 0,
    game_defensive_sacks INT DEFAULT 0,
    game_tackles INT DEFAULT 0,
    game_tackles_for_loss INT DEFAULT 0,
    game_fumbles INT DEFAULT 0,
    game_forced_fumbles INT DEFAULT 0,
    game_fumble_recoveries INT DEFAULT 0,
    game_special_teams_returns INT DEFAULT 0,
    game_special_teams_touchdowns INT DEFAULT 0,
    game_special_teams_yards INT DEFAULT 0,
    game_punting_yards INT DEFAULT 0,
    game_punting_attempts INT DEFAULT 0,
    game_kicking_attempts INT DEFAULT 0,
    game_kicking_made INT DEFAULT 0,
    game_extra_point_attempts INT DEFAULT 0,
    game_extra_points_made INT DEFAULT 0,
    PRIMARY KEY (player_id, week, season, home_team),
    FOREIGN KEY (player_id) REFERENCES Player(player_id),
    FOREIGN KEY (player_name, player_number) REFERENCES Player(name, number),
    FOREIGN KEY (week, season, home_team) REFERENCES Games(week, season, home_team)
);

CREATE TABLE offensive_stats (
    stat_name VARCHAR(50) PRIMARY KEY
);

CREATE TABLE defensive_stats (
    stat_name VARCHAR(50) PRIMARY KEY
);

CREATE TABLE special_teams_stats (
    stat_name VARCHAR(50) PRIMARY KEY
);

-- ============================================================
-- TRIGGER: Prevent duplicate jersey numbers on same team/season
-- ============================================================

CREATE OR REPLACE FUNCTION check_no_dupe_player()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM PlaysFor f
        WHERE f.team_id = NEW.team_id
        AND f.season = NEW.season
        AND f.player_number = NEW.player_number
    ) THEN
        RAISE EXCEPTION 'ERROR: Jersey number % already taken on this team for season %',
            NEW.player_number, NEW.season;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER no_dupe_player
BEFORE INSERT ON PlaysFor
FOR EACH ROW
EXECUTE FUNCTION check_no_dupe_player();

-- ============================================================
-- TRIGGER: Update season stats after a game entry is inserted
-- ============================================================

CREATE OR REPLACE FUNCTION update_player_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM season_stats s1
        WHERE s1.player_name = NEW.player_name
        AND s1.player_number = NEW.player_number
        AND s1.season = NEW.season
    ) THEN
        UPDATE season_stats SET
            season_rushing_yards            = season_rushing_yards            + NEW.game_rushing_yards,
            season_rushing_attempts         = season_rushing_attempts         + NEW.game_rushing_attempts,
            season_rushing_touchdowns       = season_rushing_touchdowns       + NEW.game_rushing_touchdowns,
            season_receiving_yards          = season_receiving_yards          + NEW.game_receiving_yards,
            season_receiving_attempts       = season_receiving_attempts       + NEW.game_receiving_attempts,
            season_receiving_touchdowns     = season_receiving_touchdowns     + NEW.game_receiving_touchdowns,
            season_passing_yards            = season_passing_yards            + NEW.game_passing_yards,
            season_passing_attempts         = season_passing_attempts         + NEW.game_passing_attempts,
            season_passing_completions      = season_passing_completions      + NEW.game_passing_completions,
            season_passing_touchdowns       = season_passing_touchdowns       + NEW.game_passing_touchdowns,
            season_offensive_interceptions  = season_offensive_interceptions  + NEW.game_offensive_interceptions,
            season_defensive_interceptions  = season_defensive_interceptions  + NEW.game_defensive_interceptions,
            season_offensive_sacks          = season_offensive_sacks          + NEW.game_offensive_sacks,
            season_defensive_sacks          = season_defensive_sacks          + NEW.game_defensive_sacks,
            season_tackles                  = season_tackles                  + NEW.game_tackles,
            season_tackles_for_loss         = season_tackles_for_loss         + NEW.game_tackles_for_loss,
            season_fumbles                  = season_fumbles                  + NEW.game_fumbles,
            season_forced_fumbles           = season_forced_fumbles           + NEW.game_forced_fumbles,
            season_fumble_recoveries        = season_fumble_recoveries        + NEW.game_fumble_recoveries,
            season_special_teams_returns    = season_special_teams_returns    + NEW.game_special_teams_returns,
            season_special_teams_touchdowns = season_special_teams_touchdowns + NEW.game_special_teams_touchdowns,
            season_special_teams_yards      = season_special_teams_yards      + NEW.game_special_teams_yards,
            season_punting_yards            = season_punting_yards            + NEW.game_punting_yards,
            season_punting_attempts         = season_punting_attempts         + NEW.game_punting_attempts,
            season_kicking_attempts         = season_kicking_attempts         + NEW.game_kicking_attempts,
            season_kicking_made             = season_kicking_made             + NEW.game_kicking_made,
            season_extra_point_attempts     = season_extra_point_attempts     + NEW.game_extra_point_attempts,
            season_extra_points_made        = season_extra_points_made        + NEW.game_extra_points_made
        WHERE (player_id = NEW.player_id OR (player_name = NEW.player_name AND player_number = NEW.player_number))
        AND season = NEW.season;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_player_stats
AFTER INSERT ON Played_In
FOR EACH ROW
EXECUTE FUNCTION update_player_stats();