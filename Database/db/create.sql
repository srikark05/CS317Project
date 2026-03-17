
CREATE TABLE Team (
    name VARCHAR(100) PRIMARY KEY,
    division VARCHAR(100),
    location VARCHAR(100),
    titles INT,
    owner VARCHAR(100),
    tv_tag VARCHAR(3)
);

CREATE TABLE Player (
    name VARCHAR(100),
    dob DATE,
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


CREATE TABLE Played_In (
    player_name VARCHAR(100),
    player_dob DATE,
    game DATE,
    Week INT,
    home_team VARCHAR(100)

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
'I need to finish including the stats because idk how to set up the ISAs'

CREATE TABLE Passing_Stat (
    stat_id INT PRIMARY KEY,
    player_name VARCHAR(100),
    player_dob DATE,
    game_id INT,
    yards INT,
    touchdowns INT,
    interceptions INT,

    FOREIGN KEY (player_name, player_dob)
        REFERENCES Player(name, dob),

    FOREIGN KEY (game_id)
        REFERENCES Games(game_id)
);

CREATE TABLE Rushing_Stat (
    stat_id INT PRIMARY KEY,
    player_name VARCHAR(100),
    player_dob DATE,
    game_id INT,
    yards INT,
    touchdowns INT,

    FOREIGN KEY (player_name, player_dob)
        REFERENCES Player(name, dob),

    FOREIGN KEY (game_id)
        REFERENCES Games(game_id)
);

CREATE TABLE Receiving_Stat (
    stat_id INT PRIMARY KEY,
    player_name VARCHAR(100),
    player_dob DATE,
    game_id INT,
    yards INT,
    touchdowns INT,

    FOREIGN KEY (player_name, player_dob)
        REFERENCES Player(name, dob),

    FOREIGN KEY (game_id)
        REFERENCES Games(game_id)
);