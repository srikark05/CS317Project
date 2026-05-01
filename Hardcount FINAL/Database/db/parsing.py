from pathlib import Path
import pandas as pd

folder = Path("../Data")

SKIP_FILES = {
    "wnfc_player_stats_master.csv",
    "wnfc_teams_master.csv",
    "wnfc_games_master.csv",
}

player_dfs = []
team_dfs = []
game_dfs = []

for file in folder.rglob("*.csv"):
    if file.name in SKIP_FILES:
        continue

    df = pd.read_csv(file)

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    filename = file.stem
    season = None
    file_type = None

    if " - " in filename:
        left, right = filename.split(" - ", 1)
        left_parts = left.split("-")
        if len(left_parts) >= 2:
            season = left_parts[-1]
        file_type = right.strip()
    else:
        parts = filename.split("-")
        if len(parts) >= 3:
            season = parts[1]
            file_type = "-".join(parts[2:])

    if season is None or file_type is None:
        raise ValueError(f"Unexpected filename format: {filename}")

    df["season"] = int(season)

    if file_type.lower() == "teams":
        team_dfs.append(df)
    elif file_type.lower() == "games":
        game_dfs.append(df)
    else:
        df["team"] = file_type.strip()
        player_dfs.append(df)

if player_dfs:
    pd.concat(player_dfs, ignore_index=True).to_csv(
        "../Data/wnfc_player_stats_master.csv", index=False
    )
    print(f"Player stats master: {sum(len(d) for d in player_dfs)} rows")

if team_dfs:
    pd.concat(team_dfs, ignore_index=True).to_csv(
        "../Data/wnfc_teams_master.csv", index=False
    )
    print(f"Teams master: {sum(len(d) for d in team_dfs)} rows")

if game_dfs:
    pd.concat(game_dfs, ignore_index=True).to_csv(
        "../Data/wnfc_games_master.csv", index=False
    )
    print(f"Games master: {sum(len(d) for d in game_dfs)} rows")
