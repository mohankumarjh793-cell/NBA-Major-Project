import pandas as pd
import time

from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats


# ============================================================
# NBA MULTI-SEASON PLAYER DATA COLLECTION
# ============================================================

OUTPUT_FILE = "data/nba_season_players.csv"


# Players we want to collect
PLAYER_NAMES = [
    "LeBron James",
    "Stephen Curry",
    "Kevin Durant",
    "Nikola Jokic",
    "Giannis Antetokounmpo",
    "Luka Doncic",
    "Jayson Tatum",
    "Joel Embiid",
    "Shai Gilgeous-Alexander",
    "Anthony Davis",
    "Damian Lillard",
    "Kawhi Leonard",
    "Jimmy Butler",
    "Devin Booker",
    "Anthony Edwards"
]


# ============================================================
# FIND NBA PLAYER ID
# ============================================================

def get_player_id(player_name):

    all_players = players.get_players()

    for player in all_players:

        if player["full_name"].lower() == player_name.lower():
            return player["id"]

    return None


# ============================================================
# COLLECT PLAYER CAREER DATA
# ============================================================

all_data = []


print("=" * 70)
print("NBA MULTI-SEASON DATA COLLECTION")
print("=" * 70)

for player_name in PLAYER_NAMES:

    print()
    print(f"Collecting data for: {player_name}")

    player_id = get_player_id(player_name)

    if player_id is None:

        print(f"Player not found: {player_name}")
        continue

    try:

        career = playercareerstats.PlayerCareerStats(
            player_id=player_id
        )

        career_data = career.get_data_frames()[0]

        for _, row in career_data.iterrows():

            season = row.get("SEASON_ID", "")

            games = row.get("GP", 0)

            points = row.get("PTS", 0)
            rebounds = row.get("REB", 0)
            assists = row.get("AST", 0)
            steals = row.get("STL", 0)
            blocks = row.get("BLK", 0)

            fg_percentage = row.get("FG_PCT", 0)
            ts_percentage = row.get("TS_PCT", 0)

            all_data.append({
                "Player": player_name,
                "Season": season,
                "Games": games,
                "Points": points,
                "Rebounds": rebounds,
                "Assists": assists,
                "Steals": steals,
                "Blocks": blocks,
                "FG_Percentage": round(
                    fg_percentage * 100, 2
                ) if pd.notna(fg_percentage) else 0,
                "TS_Percentage": round(
                    ts_percentage * 100, 2
                ) if pd.notna(ts_percentage) else 0
            })

        print(
            f"Successfully collected: {player_name}"
        )

    except Exception as error:

        print(
            f"Error collecting {player_name}: {error}"
        )

    time.sleep(1)


# ============================================================
# CREATE DATAFRAME
# ============================================================

if all_data:

    df = pd.DataFrame(all_data)

    df = df.drop_duplicates(
        subset=["Player", "Season"]
    )

    df = df.sort_values(
        by=["Player", "Season"]
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("DATA COLLECTION COMPLETED")
    print("=" * 70)

    print()
    print(
        f"Total records collected: {len(df)}"
    )

    print(
        f"Total players: {df['Player'].nunique()}"
    )

    print(
        f"Total seasons: {df['Season'].nunique()}"
    )

    print()
    print(
        f"File saved to: {OUTPUT_FILE}"
    )

else:

    print()
    print("No data was collected.")

print()
print("=" * 70)
