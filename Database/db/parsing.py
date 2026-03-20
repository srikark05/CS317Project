from pathlib import Path
import pandas as pd

folder = Path("../Data")

all_dfs = []

for file in folder.rglob("*.csv"):
    if file.name == "wnfc_player_stats_master.csv":
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
    team = None

    if " - " in filename:
        left, team = filename.split(" - ", 1)
        left_parts = left.split("-")
        if len(left_parts) >= 2:
            season = left_parts[-1]
    else:
        parts = filename.split("-")
        if len(parts) >= 3:
            season = parts[1]
            team = "-".join(parts[2:])

    if season is None or team is None:
        raise ValueError(f"Unexpected filename format: {filename}")

    df["season"] = int(season)
    df["team"] = team.strip()

    all_dfs.append(df)

master_df = pd.concat(all_dfs, ignore_index=True)

master_df.to_csv("../Data/wnfc_player_stats_master.csv", index=False)