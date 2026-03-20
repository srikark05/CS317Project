DROP TABLE IF EXISTS special_teams_stats;
DROP TABLE IF EXISTS defensive_stats;
DROP TABLE IF EXISTS offensive_stats;
DROP TABLE IF EXISTS Played_In;
DROP TABLE IF EXISTS season_stats;
DROP TABLE IF EXISTS CoachesFor;
DROP TABLE IF EXISTS PlaysFor;
DROP TABLE IF EXISTS Trade;
DROP TABLE IF EXISTS Games;
DROP TABLE IF EXISTS Staff;
DROP TABLE IF EXISTS Coach;
DROP TABLE IF EXISTS Player;
DROP TABLE IF EXISTS Special_Teams;
DROP TABLE IF EXISTS Defense;
DROP TABLE IF EXISTS Offense;
DROP TABLE IF EXISTS Positions;
DROP TABLE IF EXISTS Team;

CREATE TABLE Team (
    Team_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    division VARCHAR(100),
    address VARCHAR(100),
    titles INT DEFAULT 0,
    president VARCHAR(100),
    tv_tag VARCHAR(10)
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
    name VARCHAR(100) NOT NULL,
    number INT NOT NULL,
    dob DATE,
    position VARCHAR(2),
    weight INT,
    height INT,
    war FLOAT,
    PRIMARY KEY (name, number),
    FOREIGN KEY (position) REFERENCES Positions(position)
);

CREATE TABLE Coach (
    name VARCHAR(100) NOT NULL,
    dob DATE NOT NULL,
    record VARCHAR(50),
    PRIMARY KEY (name, dob)
);

CREATE TABLE Staff (
    staff_id INT NOT NULL,
    team_id INT NOT NULL,
    PRIMARY KEY (staff_id, team_id),
    FOREIGN KEY (team_id) REFERENCES Team(Team_id)
);

CREATE TABLE Games (
    week INT NOT NULL,
    season INT NOT NULL,
    play_date DATE NOT NULL,
    date_time TIMESTAMP NULL,
    address VARCHAR(100),
    score VARCHAR(20),
    home_team INT NOT NULL,
    away_team INT,
    PRIMARY KEY (week, season, home_team, play_date),
    FOREIGN KEY (home_team) REFERENCES Team(Team_id),
    FOREIGN KEY (away_team) REFERENCES Team(Team_id)
);

CREATE TABLE Trade (
    team_from INT NOT NULL,
    team_to INT NOT NULL,
    trade_date DATE NOT NULL,
    trade_time TIMESTAMP NOT NULL,
    team_from_players VARCHAR(1000),
    team_to_player VARCHAR(1000),
    team_to_cash DECIMAL(12,2),
    PRIMARY KEY (team_from, team_to, trade_date, trade_time),
    FOREIGN KEY (team_from) REFERENCES Team(Team_id),
    FOREIGN KEY (team_to) REFERENCES Team(Team_id)
);

CREATE TABLE PlaysFor (
    player_name VARCHAR(100) NOT NULL,
    player_number INT NOT NULL,
    team_id INT NOT NULL,
    season INT NOT NULL,
    position VARCHAR(2),
    PRIMARY KEY (player_name, player_number, team_id, season),
    FOREIGN KEY (player_name, player_number) REFERENCES Player(name, number),
    FOREIGN KEY (team_id) REFERENCES Team(Team_id),
    FOREIGN KEY (position) REFERENCES Positions(position)
);

CREATE TABLE CoachesFor (
    coach_name VARCHAR(100) NOT NULL,
    coach_dob DATE NOT NULL,
    team_id INT NOT NULL,
    season INT NOT NULL,
    PRIMARY KEY (coach_name, coach_dob, team_id, season),
    FOREIGN KEY (coach_name, coach_dob) REFERENCES Coach(name, dob),
    FOREIGN KEY (team_id) REFERENCES Team(Team_id)
);

CREATE TABLE season_stats (
    player_name VARCHAR(100) NOT NULL,
    player_number INT NOT NULL,
    season INT NOT NULL,
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
    season_tackles DECIMAL(8,2) DEFAULT 0,
    season_tackles_for_loss DECIMAL(8,2) DEFAULT 0,
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
    PRIMARY KEY (player_name, player_number, season),
    FOREIGN KEY (player_name, player_number) REFERENCES Player(name, number)
);

CREATE TABLE Played_In (
    player_name VARCHAR(100) NOT NULL,
    player_number INT NOT NULL,
    game_date DATE NOT NULL,
    week INT NOT NULL,
    season INT NOT NULL,
    home_team INT NOT NULL,
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
    game_tackles DECIMAL(8,2) DEFAULT 0,
    game_tackles_for_loss DECIMAL(8,2) DEFAULT 0,
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
    PRIMARY KEY (player_name, player_number, game_date, week, season, home_team),
    FOREIGN KEY (player_name, player_number) REFERENCES Player(name, number),
    FOREIGN KEY (week, season, home_team, game_date) REFERENCES Games(week, season, home_team, play_date)
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