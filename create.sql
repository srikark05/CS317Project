
CREATE TABLE Team (
    name VARCHAR(100),
    Team_id INT PRIMARY KEY,
    division VARCHAR(100),
    adress VARCHAR(100),
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
    name VARCHAR(100),
    dob DATE,
    position VARCHAR(2),
    number INT,
    weight INT,
    height INT,
    war FLOAT,
    PRIMARY KEY (name, number)
);

CREATE TABLE Coach (
    name VARCHAR(100),
    dob DATE,
    record VARCHAR(50),
    PRIMARY KEY (name, dob)
);

CREATE TABLE Staff (
    staff_id INT ,
    team_id INT,

    FOREIGN KEY team_id INT
        REFERENCES Team(id),
    PRIMARY KEY (staff_id, team_id)
);

CREATE TABLE Games (
    week INT,
    season INT,
    day play_date DATE,
    date_time TIMESTAMP,
    adress VARCHAR(100),
    score VARCHAR(20)
    FOREIGN KEY home_team INT
        REFERENCES Team(Team_id),
    FOREIGN KEY away_team INT        
        REFERENCES Team(Team_id)
PRIMARY KEY (week, season, home_team)
);

CREATE TABLE Trade (
    team_from INT,
    team_to INT,
    trade_date DATE,
    trade_time TIMESTAMP,
    team_from_players VARCHAR(1000),
    team_to_player VARCHAR(1000),
    team_to_cash DECIMAL(12,2),

    FOREIGN KEY (team_from) REFERENCES Team(Team_id),
    FOREIGN KEY (team_to) REFERENCES Team(Team_id)

    PRIMARY KEY (team_from, team_to, trade_date, trade_time)
);

CREATE TABLE PlaysFor (
    player_name VARCHAR(100),
    player_number INT,
    team_name INT,
    season INT,
    

    PRIMARY KEY (player_name, player_number, team_id, season),

    FOREIGN KEY (player_name, player_number)
        REFERENCES Player(name, number),

    FOREIGN KEY (team_name) INT
        REFERENCES Team(Team_id)

     FOREIGN KEY  (position) REFERENCES Positions(position)
);


CREATE TABLE CoachesFor (
    coach_name VARCHAR(100),
    coach_dob DATE,
    team_name INT,
    season INT,

    PRIMARY KEY (coach_name, coach_dob, team_name, season),

    FOREIGN KEY (coach_name, coach_dob)
        REFERENCES Coach(name, dob),

    FOREIGN KEY (team_name)
        REFERENCES Team(Team_id)
);

Create Table season_stats(
    player_name VARCHAR(100),
    player_number INT,
    season INT,
    season_rushing_yards INT,
    season_rushing_attempts INT,
    season_rushing_touchdowns INT,
    season_receiving_yards INT,
    season_receiving_attempts INT,
    season_receiving_touchdowns INT,
    season_passing_yards INT,
    season_passing_attempts INT,
    season_passing_completions INT,
    season_passing_touchdowns INT,
    season_offensive_interceptions INT,
    season_defensive_interceptions INT,
    season_offensive_sacks INT,
    season_defensive_sacks INT,
    season_tackles INT,
    season_tackles_for_loss INT,
    season_fumbles INT,
    season_forced_fumbles INT,
    season_fumble_recoveries INT,
    season_special_teams_returns INT,
    season_special_teams_touchdowns INT,
    season_special_teams_yards INT,
    season_punting_yards INT,
    season_punting_attempts INT,
    season_kicking_attempts INT,
    season_kicking_made INT,
    season_extra_point_attempts INT,
    season_extra_points_made INT,

     PRIMARY KEY (player_name, player_number,season),

     FOREIGN KEY (player_name, player_number)
        REFERENCES Player(name, number));

CREATE TABLE Played_In (
    player_name VARCHAR(100),
    player_number INT,
    --changed from just game ->game_date
    game_date DATE,
    Week INT,
    home_team VARCHAR(100)
    game_rushing_yards INT,
    game_rushing_attempts INT,
    game_rushing_touchdowns INT,
    game_receiving_yards INT,
    game_receiving_attempts INT,
    game_receiving_touchdowns INT,
    game_passing_yards INT,
    game_passing_attempts INT,
    game_passing_completions INT,
    game_passing_touchdowns INT,
    game_offensive_interceptions INT,
    game_defensive_interceptions INT,
    game_offensive_sacks INT,
    game_defensive_sacks INT,
    game_tackles INT,
    game_tackles_for_loss INT,
    game_fumbles INT,
    game_forced_fumbles INT,
    game_fumble_recoveries INT,
    game_special_teams_returns INT,
    game_special_teams_touchdowns INT,
    game_special_teams_yards INT,
    game_punting_yards INT,
    game_punting_attempts INT,
    game_kicking_attempts INT,
    game_kicking_made INT,
    game_extra_point_attempts INT,
    game_extra_points_made INT,
    PRIMARY KEY (player_name, player_number, game),

    FOREIGN KEY (player_name, player_number)
        REFERENCES Player(name, number),

    FOREIGN KEY (game)
        REFERENCES Game(play_date)
    FOREIGN KEY (week)
        REFERENCES Game(week)
    FOREIGN KEY (home_team)
        REFERENCES Game(home_team)
);
offensive_stats(
    stat_name VARCHAR(50) PRIMARY KEY
);
defensive_stats(
    stat_name VARCHAR(50) PRIMARY KEY
);
special_teams_stats(
    stat_name VARCHAR(50) PRIMARY KEY
);


--trigger to prevent two players with the same number on the same team
CREATE TRIGGER no_dupe_player
BEFORE INSERT ON PlaysFor
FOR EACH ROW
BEGIN
    IF NEW.player_number IN (
        SELECT player_number
        FROM PlaysFor f
        WHERE (f.team_name = NEW.team_name)
        AND (f.season = NEW.season)
    ) THEN (
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Jersey number already taken on this team';
    ) END IF;
END;

--update player stats after playing in a game
--currently assumes player already has a row entry
CREATE TRIGGER update_player_stats
AFTER INSERT ON Played_In
FOR EACH ROW
BEGIN
    IF EXISTS
        (SELECT *
        FROM season_stats s1
        WHERE (NEW.player_name = s1.player_name)
        AND (NEW.player_number = s1.player_number))
    THEN
        UPDATE season_stats s2 SET
        season_rushing_yards            = s2.season_rushing_yards               + NEW.game_rushing_yards,
        season_rushing_attempts         = s2.season_rushing_attempts            + NEW.game_rushing_attempts,
        season_rushing_touchdowns       = s2.season_rushing_touchdowns          + NEW.game_rushing_touchdowns,
        season_receiving_yards          = s2.season_receiving_yards             + NEW.game_receiving_yards,
        season_receiving_attempts       = s2.season_receiving_attempts          + NEW.game_receiving_attempts,
        season_receiving_touchdowns     = s2.season_receiving_touchdowns        + NEW.game_receiving_touchdowns,
        season_passing_yards            = s2.season_passing_yards               + NEW.game_passing_yards,
        season_passing_attempts         = s2.season_passing_attempts            + NEW.game_passing_attempts,
        season_passing_completions      = s2.season_passing_completions         + NEW.game_passing_completions,
        season_passing_touchdowns       = s2.season_passing_touchdowns          + NEW.game_passing_touchdowns,
        season_offensive_interceptions  = s2.season_offensive_interceptions     + NEW.game_offensive_interceptions,
        season_defensive_interceptions  = s2.season_defensive_interceptions     + NEW.game_defensive_interceptions,
        season_offensive_sacks          = s2.season_offensive_sacks             + NEW.game_offensive_sacks,
        season_defensive_sacks          = s2.season_defensive_sacks             + NEW.game_defensive_sacks,
        season_tackles                  = s2.season_tackles                     + NEW.game_tackles,
        season_tackles_for_loss         = s2.season_tackles_for_loss            + NEW.game_tackles_for_loss,
        season_fumbles                  = s2.season_fumbles                     + NEW.game_fumbles,
        season_forced_fumbles           = s2.season_forced_fumbles              + NEW.game_forced_fumbles,
        season_fumble_recoveries        = s2.season_fumble_recoveries           + NEW.game_fumble_recoveries,
        season_special_teams_returns    = s2.season_special_teams_returns       + NEW.game_special_teams_returns,
        season_special_teams_touchdowns = s2.season_special_teams_touchdowns    + NEW.game_special_teams_touchdowns,
        season_special_teams_yards      = s2.season_special_teams_yards         + NEW.game_special_teams_yards,
        season_punting_yards            = s2.season_punting_yards               + NEW.game_punting_yards,
        season_punting_attempts         = s2.season_punting_attempts            + NEW.game_punting_attempts,
        season_kicking_attempts         = s2.season_kicking_attempts            + NEW.game_kicking_attempts,
        season_kicking_made             = s2.season_kicking_made                + NEW.game_kicking_made,
        season_extra_point_attempts     = s2.season_extra_point_attempts        + NEW.game_extra_point_attempts,
        season_extra_points_made        = s2.season_extra_points_made           + NEW.game_extra_points_made
        --jesus christ
        WHERE (s2.player_name = NEW.player_name)
        AND (s2.player_number = NEW.player_number)
        --matches date to extract season
        AND (s2.season IN (
            SELECT season
            FROM Games 
            WHERE (play_date = NEW.game_date)))
    END IF;
END;






