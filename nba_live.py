import requests
from datetime import datetime, timedelta


ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"


def get_games_for_date(date):
    try:
        params = {
            "dates": date.strftime("%Y%m%d"),
            "limit": 100
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        response = requests.get(
            ESPN_URL,
            params=params,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            print("ESPN API HTTP Error:", response.status_code)
            return []

        data = response.json()

        events = data.get("events", [])
        results = []

        for event in events:

            competitions = event.get("competitions", [])

            if not competitions:
                continue

            competition = competitions[0]

            competitors = competition.get("competitors", [])

            home_team = {}
            away_team = {}

            for team in competitors:

                team_data = team.get("team", {})

                team_info = {
                    "name": team_data.get("displayName", "Unknown Team"),
                    "short_name": team_data.get("abbreviation", ""),
                    "score": team.get("score", "0")
                }

                if team.get("homeAway") == "home":
                    home_team = team_info
                else:
                    away_team = team_info

            status = event.get("status", {})
            status_type = status.get("type", {})

            results.append({
                "game_id": event.get("id"),

                "home_team": home_team.get(
                    "name",
                    "Home Team"
                ),

                "home_score": home_team.get(
                    "score",
                    "0"
                ),

                "away_team": away_team.get(
                    "name",
                    "Away Team"
                ),

                "away_score": away_team.get(
                    "score",
                    "0"
                ),

                "game_status": status_type.get(
                    "shortDetail",
                    "Scheduled"
                ),

                "game_state": status_type.get(
                    "state",
                    "pre"
                ),

                "game_time": event.get(
                    "date",
                    ""
                )
            })

        return results

    except requests.exceptions.Timeout:
        print("ESPN API Error: Request timed out.")
        return []

    except requests.exceptions.RequestException as e:
        print("ESPN API Connection Error:", e)
        return []

    except ValueError:
        print("ESPN API Error: Invalid JSON response.")
        return []

    except Exception as e:
        print("ESPN API Error:", e)
        return []


def get_live_games():

    today = datetime.now()

    games = get_games_for_date(today)

    live_games = []

    for game in games:

        if game["game_state"] == "in":

            live_games.append(game)

    return live_games


def get_upcoming_games():

    today = datetime.now()

    upcoming_games = []

    for i in range(0, 8):

        date = today + timedelta(days=i)

        games = get_games_for_date(date)

        for game in games:

            if game["game_state"] == "pre":

                upcoming_games.append(game)

    return upcoming_games


def get_all_games():

    today = datetime.now()

    all_games = []

    for i in range(0, 8):

        date = today + timedelta(days=i)

        games = get_games_for_date(date)

        all_games.extend(games)

    return all_games


if __name__ == "__main__":

    print("=" * 60)
    print("NBA LIVE DATA TEST")
    print("=" * 60)

    live_games = get_live_games()

    print()
    print("LIVE GAMES:")

    if live_games:

        for game in live_games:

            print(
                f"{game['away_team']} "
                f"{game['away_score']} - "
                f"{game['home_score']} "
                f"{game['home_team']}"
            )

            print(
                f"Status: {game['game_status']}"
            )

    else:

        print("No live NBA games right now.")

    print()
    print("=" * 60)

    upcoming_games = get_upcoming_games()

    print()
    print("UPCOMING GAMES:")

    if upcoming_games:

        for game in upcoming_games:

            print(
                f"{game['away_team']} "
                f"vs "
                f"{game['home_team']}"
            )

            print(
                f"Time: {game['game_time']}"
            )

            print(
                f"Status: {game['game_status']}"
            )

            print()

    else:

        print("No upcoming NBA games found.")

    print("=" * 60)