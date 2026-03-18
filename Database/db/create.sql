
CREATE TABLE Team (
    name VARCHAR(100) PRIMARY KEY,
    division VARCHAR(100),
    location VARCHAR(100),
    titles INT,
    owner VARCHAR(100),
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
    PRIMARY KEY (name, dob)
);

CREATE TABLE Coach (
    name VARCHAR(100),
    dob DATE,
    record VARCHAR(50),
    PRIMARY KEY (name, dob)
);

CREATE TABLE Staff (
    staff_id INT ,
    name VARCHAR(100),

    FOREIGN KEY team_name VARCHAR(100)
        REFERENCES Team(name),
    PRIMARY KEY (staff_id, team_name)
);

CREATE TABLE Games (
    week INT,
    season INT,
    day play_date DATE,
    date_time TIMESTAMP,
    location VARCHAR(100),
    score VARCHAR(20)
    FOREIGN KEY home_team VARCHAR(100)
        REFERENCES Team(name),
    FOREIGN KEY away_team VARCHAR(100)        
        REFERENCES Team(name)
PRIMARY KEY (week, season, home_team)
);

CREATE TABLE Trade (
    team_from VARCHAR(100),
    team_to VARCHAR(100),
    trade_date DATE,
    trade_time TIMESTAMP,
    team_from_players VARCHAR(1000),
    team_to_player VARCHAR(1000),
    team_to_cash DECIMAL(12,2),

    FOREIGN KEY (team_from) REFERENCES Team(name),
    FOREIGN KEY (team_to) REFERENCES Team(name)

    PRIMARY KEY (team_from, team_to, trade_date, trade_time)
);

CREATE TABLE PlaysFor (
    player_name VARCHAR(100),
    player_dob DATE,
    team_name VARCHAR(100),
    season INT,
    

    PRIMARY KEY (player_name, player_dob, team_name, season),

    FOREIGN KEY (player_name, player_dob)
        REFERENCES Player(name, dob),

    FOREIGN KEY (team_name)
        REFERENCES Team(name)

     FOREIGN KEY  (position) REFERENCES Positions(position)
);


CREATE TABLE CoachesFor (
    coach_name VARCHAR(100),
    coach_dob DATE,
    team_name VARCHAR(100),
    season INT,

    PRIMARY KEY (coach_name, coach_dob, team_name, season),

    FOREIGN KEY (coach_name, coach_dob)
        REFERENCES Coach(name, dob),

    FOREIGN KEY (team_name)
        REFERENCES Team(name)
);

Create Table season_stats(
    player_name VARCHAR(100),
    player_dob DATE,
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

     PRIMARY KEY (player_name, player_dob,season),

     FOREIGN KEY (player_name, player_dob)
        REFERENCES Player(name, dob);

CREATE TABLE Played_In (
    player_name VARCHAR(100),
    player_dob DATE,
    game DATE,
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
    PRIMARY KEY (player_name, player_dob, game),

    FOREIGN KEY (player_name, player_dob)
        REFERENCES Player(name, dob),

    FOREIGN KEY (game)
        REFERENCES Game(play_date)
    FOREIGN KEY (week)
        REFERENCES Game(week)
    FOREIGN KEY (home_team)
        REFERENCES Game(home_team)
);