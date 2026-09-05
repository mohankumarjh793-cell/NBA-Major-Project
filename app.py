from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import pandas as pd
import os
import sqlite3

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from nba_live import get_live_games


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = "nba_major_project_secret_key"


# ============================================================
# MAIN DATA FILE
# ============================================================

DATA_FILE = os.path.join(
    "data",
    "nba_players.csv"
)

df = pd.read_csv(DATA_FILE)


# ============================================================
# DATABASE
# ============================================================

DATABASE_FILE = "database.db"


def get_db_connection():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    connection = get_db_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            player1 TEXT NOT NULL,
            player2 TEXT NOT NULL,
            winner TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    connection.commit()

    connection.close()


initialize_database()


# ============================================================
# ML MODEL
# ============================================================

def train_prediction_model():

    features = [

        "Points",
        "Rebounds",
        "Assists",
        "Steals",
        "Blocks",
        "FG_Percentage",
        "TS_Percentage",
        "PER"

    ]

    target = "Win_Shares"

    clean_df = df.dropna(
        subset=features + [target]
    ).copy()

    X = clean_df[features]

    y = clean_df[target]


    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )

    model.fit(
        X,
        y
    )


    if len(clean_df) >= 5:

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42
        )

        evaluation_model = RandomForestRegressor(
            n_estimators=200,
            random_state=42
        )

        evaluation_model.fit(
            X_train,
            y_train
        )

        predictions = evaluation_model.predict(
            X_test
        )

        mae = mean_absolute_error(
            y_test,
            predictions
        )

        mse = mean_squared_error(
            y_test,
            predictions
        )

        r2 = r2_score(
            y_test,
            predictions
        )

    else:

        mae = 0
        mse = 0
        r2 = 0


    return (
        model,
        mae,
        mse,
        r2,
        features
    )


# ============================================================
# PERFORMANCE RANKING
# ============================================================

def calculate_performance_ranking():

    ranking_df = df.copy()

    metrics = {

        "Points": 20,
        "Rebounds": 10,
        "Assists": 10,
        "Steals": 5,
        "Blocks": 5,
        "FG_Percentage": 10,
        "TS_Percentage": 10,
        "PER": 15,
        "Win_Shares": 15

    }

    ranking_df["Performance_Score"] = 0.0


    for column, weight in metrics.items():

        minimum = ranking_df[column].min()

        maximum = ranking_df[column].max()


        if maximum == minimum:

            normalized = 100

        else:

            normalized = (
                (ranking_df[column] - minimum)
                / (maximum - minimum)
            ) * 100


        ranking_df["Performance_Score"] += (
            normalized * (weight / 100)
        )


    ranking_df = ranking_df.sort_values(
        by="Performance_Score",
        ascending=False
    ).reset_index(drop=True)


    ranking_df["Rank"] = (
        ranking_df.index + 1
    )


    ranking_df["Performance_Score"] = (
        ranking_df["Performance_Score"]
        .round(2)
    )


    return ranking_df


# ============================================================
# PLAYER PROFILE ANALYTICS
# ============================================================

def get_player_profile_analytics(player_name):

    ranking_df = calculate_performance_ranking()


    player_result = ranking_df[
        ranking_df["Player"].str.lower()
        == player_name.lower()
    ]


    if player_result.empty:

        return None


    player_row = player_result.iloc[0]


    total_players = len(
        ranking_df
    )


    player_rank = int(
        player_row["Rank"]
    )


    performance_score = float(
        player_row["Performance_Score"]
    )


    if total_players <= 1:

        percentile = 100.0

    else:

        percentile = (
            (total_players - player_rank)
            / (total_players - 1)
        ) * 100


    percentile = round(
        percentile,
        1
    )


    dataset_averages = {

        "Points": round(
            df["Points"].mean(),
            2
        ),

        "Rebounds": round(
            df["Rebounds"].mean(),
            2
        ),

        "Assists": round(
            df["Assists"].mean(),
            2
        ),

        "Steals": round(
            df["Steals"].mean(),
            2
        ),

        "Blocks": round(
            df["Blocks"].mean(),
            2
        ),

        "FG_Percentage": round(
            df["FG_Percentage"].mean(),
            2
        ),

        "TS_Percentage": round(
            df["TS_Percentage"].mean(),
            2
        ),

        "PER": round(
            df["PER"].mean(),
            2
        ),

        "Win_Shares": round(
            df["Win_Shares"].mean(),
            2
        )

    }


    player_values = {

        "Points": float(
            player_row["Points"]
        ),

        "Rebounds": float(
            player_row["Rebounds"]
        ),

        "Assists": float(
            player_row["Assists"]
        ),

        "Steals": float(
            player_row["Steals"]
        ),

        "Blocks": float(
            player_row["Blocks"]
        ),

        "FG_Percentage": float(
            player_row["FG_Percentage"]
        ),

        "TS_Percentage": float(
            player_row["TS_Percentage"]
        ),

        "PER": float(
            player_row["PER"]
        ),

        "Win_Shares": float(
            player_row["Win_Shares"]
        )

    }


    comparison_to_average = {}


    for metric in player_values:

        player_value = player_values[
            metric
        ]

        average_value = dataset_averages[
            metric
        ]

        difference = (
            player_value
            - average_value
        )


        percentage_difference = 0


        if average_value != 0:

            percentage_difference = (
                difference
                / average_value
            ) * 100


        comparison_to_average[metric] = {

            "player_value": round(
                player_value,
                2
            ),

            "average_value": round(
                average_value,
                2
            ),

            "difference": round(
                difference,
                2
            ),

            "percentage_difference": round(
                percentage_difference,
                1
            )

        }


    prediction_result = None


    try:

        model, mae, mse, r2, features = (
            train_prediction_model()
        )


        input_data = pd.DataFrame(
            [[

                player_values["Points"],
                player_values["Rebounds"],
                player_values["Assists"],
                player_values["Steals"],
                player_values["Blocks"],
                player_values["FG_Percentage"],
                player_values["TS_Percentage"],
                player_values["PER"]

            ]],
            columns=features
        )


        predicted_value = model.predict(
            input_data
        )[0]


        actual_value = player_values[
            "Win_Shares"
        ]


        prediction_result = {

            "predicted": round(
                float(predicted_value),
                2
            ),

            "actual": round(
                float(actual_value),
                2
            ),

            "difference": round(
                abs(
                    float(
                        actual_value
                        - predicted_value
                    )
                ),
                2
            ),

            "mae": round(
                float(mae),
                3
            ),

            "mse": round(
                float(mse),
                3
            ),

            "r2": round(
                float(r2),
                3
            )

        }

    except Exception:

        prediction_result = None


    return {

        "rank": player_rank,

        "total_players": total_players,

        "performance_score": performance_score,

        "percentile": percentile,

        "dataset_averages": dataset_averages,

        "comparison_to_average": comparison_to_average,

        "prediction": prediction_result

    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        if not username or not email or not password:

            flash(
                "Please fill in all fields.",
                "error"
            )

            return render_template(
                "register.html"
            )


        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "register.html"
            )


        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return render_template(
                "register.html"
            )


        connection = get_db_connection()


        existing_user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            OR email = ?
            """,
            (
                username,
                email
            )
        ).fetchone()


        if existing_user:

            connection.close()

            flash(
                "Username or email already exists.",
                "error"
            )

            return render_template(
                "register.html"
            )


        hashed_password = generate_password_hash(
            password
        )


        connection.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                email,
                hashed_password
            )
        )


        connection.commit()

        connection.close()


        flash(
            "Registration successful! Please login.",
            "success"
        )


        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        if not username or not password:

            flash(
                "Please enter username and password.",
                "error"
            )

            return render_template(
                "login.html"
            )


        connection = get_db_connection()


        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()


        connection.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]


            flash(
                "Login successful!",
                "success"
            )


            return redirect(
                url_for("dashboard")
            )


        flash(
            "Invalid username or password.",
            "error"
        )


        return render_template(
            "login.html"
        )


    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()


    flash(
        "You have been logged out.",
        "success"
    )


    return redirect(
        url_for("home")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        flash(
            "Please login to access your dashboard.",
            "error"
        )

        return redirect(
            url_for("login")
        )


    connection = get_db_connection()


    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (
            session["user_id"],
        )
    ).fetchone()


    saved_comparisons = connection.execute(
        """
        SELECT *
        FROM saved_comparisons
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (
            session["user_id"],
        )
    ).fetchall()


    connection.close()


    if user is None:

        session.clear()

        return redirect(
            url_for("login")
        )


    return render_template(
        "dashboard.html",
        user=user,
        saved_comparisons=saved_comparisons
    )


# ============================================================
# PLAYER SEARCH
# ============================================================

@app.route("/search")
def search():

    player_name = request.args.get(
        "player",
        ""
    ).strip()


    if not player_name:

        return render_template(
            "home.html",
            error="Please enter a player name."
        )


    result = df[
        df["Player"].str.contains(
            player_name,
            case=False,
            na=False
        )
    ]


    return render_template(
        "home.html",
        players=result.to_dict("records"),
        search=player_name
    )


# ============================================================
# PLAYER PROFILE
# ============================================================

@app.route("/player/<path:player_name>")
def player_profile(player_name):

    result = df[
        df["Player"].str.lower()
        == player_name.lower()
    ]


    if result.empty:

        return render_template(
            "home.html",
            error="Player not found."
        )


    player = result.iloc[0].to_dict()


    profile_analytics = (
        get_player_profile_analytics(
            player_name
        )
    )


    if profile_analytics is None:

        return render_template(
            "home.html",
            error="Unable to calculate player analytics."
        )


    return render_template(
        "player.html",

        player=player,

        profile_analytics=profile_analytics,

        player_rank=profile_analytics[
            "rank"
        ],

        total_players=profile_analytics[
            "total_players"
        ],

        performance_score=profile_analytics[
            "performance_score"
        ],

        percentile=profile_analytics[
            "percentile"
        ],

        dataset_averages=profile_analytics[
            "dataset_averages"
        ],

        comparison_to_average=profile_analytics[
            "comparison_to_average"
        ],

        prediction=profile_analytics[
            "prediction"
        ]
    )


# ============================================================
# PLAYER COMPARISON
# ============================================================

@app.route(
    "/compare",
    methods=["GET", "POST"]
)
def compare():

    players = df["Player"].tolist()


    player1_name = request.values.get(
        "player1",
        ""
    ).strip()


    player2_name = request.values.get(
        "player2",
        ""
    ).strip()


    player1 = None

    player2 = None

    winners = []

    comparison = None

    analysis = None

    chart_data = None

    error = None


    if player1_name and player2_name:

        if (
            player1_name.lower()
            == player2_name.lower()
        ):

            error = (
                "Please select two different players."
            )

        else:

            result1 = df[
                df["Player"].str.lower()
                == player1_name.lower()
            ]


            result2 = df[
                df["Player"].str.lower()
                == player2_name.lower()
            ]


            if result1.empty or result2.empty:

                error = (
                    "One or both players were not found."
                )

            else:

                player1 = (
                    result1.iloc[0].to_dict()
                )

                player2 = (
                    result2.iloc[0].to_dict()
                )


                comparison = {

                    "player1": player1,

                    "player2": player2

                }


                metrics = {

                    "Scoring": "Points",

                    "Rebounding": "Rebounds",

                    "Playmaking": "Assists",

                    "Steals": "Steals",

                    "Blocks": "Blocks",

                    "FG%": "FG_Percentage",

                    "TS%": "TS_Percentage",

                    "Efficiency": "PER",

                    "Win Shares": "Win_Shares"

                }


                categories = {}


                for category, column in metrics.items():

                    value1 = float(
                        player1[column]
                    )

                    value2 = float(
                        player2[column]
                    )


                    if value1 > value2:

                        winner = player1["Player"]

                    elif value2 > value1:

                        winner = player2["Player"]

                    else:

                        winner = "Tie"


                    categories[category] = winner


                    winners.append(
                        {
                            "category": category,
                            "winner": winner
                        }
                    )


                score1 = 0

                score2 = 0


                for winner in categories.values():

                    if winner == player1["Player"]:

                        score1 += 1

                    elif winner == player2["Player"]:

                        score2 += 1


                total_categories = len(
                    categories
                )


                if total_categories > 0:

                    percentage1 = round(
                        (
                            score1
                            / total_categories
                        ) * 100,
                        1
                    )

                    percentage2 = round(
                        (
                            score2
                            / total_categories
                        ) * 100,
                        1
                    )

                else:

                    percentage1 = 0

                    percentage2 = 0


                if score1 > score2:

                    overall_winner = player1["Player"]

                elif score2 > score1:

                    overall_winner = player2["Player"]

                else:

                    overall_winner = "Tie"


                analysis = {

                    "categories": categories,

                    "score1": score1,

                    "score2": score2,

                    "percentage1": percentage1,

                    "percentage2": percentage2,

                    "overall_winner": overall_winner

                }


                chart_data = {

                    "player1_name":
                        player1["Player"],

                    "player2_name":
                        player2["Player"],

                    "labels": [

                        "Points",
                        "Rebounds",
                        "Assists",
                        "Steals",
                        "Blocks",
                        "FG%",
                        "TS%",
                        "PER",
                        "Win Shares"

                    ],

                    "player1": [

                        float(
                            player1["Points"]
                        ),

                        float(
                            player1["Rebounds"]
                        ),

                        float(
                            player1["Assists"]
                        ),

                        float(
                            player1["Steals"]
                        ),

                        float(
                            player1["Blocks"]
                        ),

                        float(
                            player1["FG_Percentage"]
                        ),

                        float(
                            player1["TS_Percentage"]
                        ),

                        float(
                            player1["PER"]
                        ),

                        float(
                            player1["Win_Shares"]
                        )

                    ],

                    "player2": [

                        float(
                            player2["Points"]
                        ),

                        float(
                            player2["Rebounds"]
                        ),

                        float(
                            player2["Assists"]
                        ),

                        float(
                            player2["Steals"]
                        ),

                        float(
                            player2["Blocks"]
                        ),

                        float(
                            player2["FG_Percentage"]
                        ),

                        float(
                            player2["TS_Percentage"]
                        ),

                        float(
                            player2["PER"]
                        ),

                        float(
                            player2["Win_Shares"]
                        )

                    ]

                }


    return render_template(

        "comparison.html",

        players=players,

        comparison=comparison,

        analysis=analysis,

        chart_data=chart_data,

        error=error,

        player1=player1,

        player2=player2,

        player1_name=player1_name,

        player2_name=player2_name,

        winners=winners

    )


# ============================================================
# SAVE COMPARISON
# ============================================================

@app.route(
    "/save-comparison",
    methods=["POST"]
)
def save_comparison():

    if "user_id" not in session:

        flash(
            "Please login to save comparisons.",
            "error"
        )

        return redirect(
            url_for("login")
        )


    player1 = request.form.get(
        "player1",
        ""
    ).strip()


    player2 = request.form.get(
        "player2",
        ""
    ).strip()


    winner = request.form.get(
        "winner",
        ""
    ).strip()


    if not player1 or not player2:

        flash(
            "Unable to save comparison.",
            "error"
        )

        return redirect(
            url_for("compare")
        )


    if not winner:

        winner = "Tie"


    connection = get_db_connection()


    connection.execute(
        """
        INSERT INTO saved_comparisons
        (
            user_id,
            player1,
            player2,
            winner
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            session["user_id"],
            player1,
            player2,
            winner
        )
    )


    connection.commit()

    connection.close()


    flash(
        "Comparison saved successfully! 💾",
        "success"
    )


    return redirect(
        url_for(
            "compare",
            player1=player1,
            player2=player2
        )
    )


# ============================================================
# DELETE COMPARISON
# ============================================================

@app.route(
    "/delete-comparison/<int:comparison_id>",
    methods=["POST"]
)
def delete_comparison(comparison_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    connection = get_db_connection()


    connection.execute(
        """
        DELETE FROM saved_comparisons
        WHERE id = ?
        AND user_id = ?
        """,
        (
            comparison_id,
            session["user_id"]
        )
    )


    connection.commit()

    connection.close()


    flash(
        "Saved comparison deleted.",
        "success"
    )


    return redirect(
        url_for("dashboard")
    )


# ============================================================
# PREDICTION
# ============================================================

@app.route(
    "/prediction",
    methods=["GET", "POST"]
)
def prediction():

    players = df["Player"].tolist()


    selected_player = request.form.get(
        "player",
        ""
    )


    prediction_result = None

    player_data = None

    mae = None

    mse = None

    r2 = None

    error = None


    if request.method == "POST":

        if not selected_player:

            error = (
                "Please select a player."
            )

        else:

            result = df[
                df["Player"].str.lower()
                == selected_player.lower()
            ]


            if result.empty:

                error = (
                    "Player not found."
                )

            else:

                try:

                    (
                        model,
                        mae,
                        mse,
                        r2,
                        features
                    ) = train_prediction_model()


                    player = result.iloc[0]


                    input_data = pd.DataFrame(
                        [[

                            float(
                                player["Points"]
                            ),

                            float(
                                player["Rebounds"]
                            ),

                            float(
                                player["Assists"]
                            ),

                            float(
                                player["Steals"]
                            ),

                            float(
                                player["Blocks"]
                            ),

                            float(
                                player["FG_Percentage"]
                            ),

                            float(
                                player["TS_Percentage"]
                            ),

                            float(
                                player["PER"]
                            )

                        ]],
                        columns=features
                    )


                    predicted_value = (
                        model.predict(
                            input_data
                        )[0]
                    )


                    actual_value = float(
                        player["Win_Shares"]
                    )


                    difference = abs(
                        actual_value
                        - predicted_value
                    )


                    prediction_result = round(
                        predicted_value,
                        2
                    )


                    player_data = {

                        "Player":
                            player["Player"],

                        "Points":
                            player["Points"],

                        "Rebounds":
                            player["Rebounds"],

                        "Assists":
                            player["Assists"],

                        "Steals":
                            player["Steals"],

                        "Blocks":
                            player["Blocks"],

                        "FG_Percentage":
                            player["FG_Percentage"],

                        "TS_Percentage":
                            player["TS_Percentage"],

                        "PER":
                            player["PER"],

                        "Win_Shares":
                            player["Win_Shares"],

                        "difference":
                            round(
                                difference,
                                2
                            )

                    }


                except Exception as e:

                    error = (
                        "Prediction error: "
                        + str(e)
                    )


    return render_template(

        "prediction.html",

        players=players,

        selected_player=selected_player,

        prediction_result=prediction_result,

        player_data=player_data,

        mae=mae,

        mse=mse,

        r2=r2,

        error=error

    )


# ============================================================
# GENERAL ANALYSIS
# ============================================================

@app.route("/analysis")
def analysis():

    total_players = len(df)


    average_points = round(
        df["Points"].mean(),
        2
    )


    average_rebounds = round(
        df["Rebounds"].mean(),
        2
    )


    average_assists = round(
        df["Assists"].mean(),
        2
    )


    average_per = round(
        df["PER"].mean(),
        2
    )


    top_scorer = df.loc[
        df["Points"].idxmax()
    ].to_dict()


    best_per = df.loc[
        df["PER"].idxmax()
    ].to_dict()


    best_win_shares = df.loc[
        df["Win_Shares"].idxmax()
    ].to_dict()


    return render_template(

        "analysis.html",

        total_players=total_players,

        average_points=average_points,

        average_rebounds=average_rebounds,

        average_assists=average_assists,

        average_per=average_per,

        top_scorer=top_scorer,

        best_per=best_per,

        best_win_shares=best_win_shares

    )


# ============================================================
# ANALYSIS API
# ============================================================

@app.route("/api/analysis-data")
def analysis_data():

    analysis_columns = [

        "Player",
        "Points",
        "Rebounds",
        "Assists",
        "Steals",
        "Blocks",
        "FG_Percentage",
        "TS_Percentage",
        "PER",
        "Win_Shares"

    ]


    data = df[
        analysis_columns
    ].to_dict("records")


    return data


# ============================================================
# PREPARE SEASON DATA
# ============================================================

def prepare_season_dataframe():

    season_file = os.path.join(
        "data",
        "nba_season_players.csv"
    )


    if not os.path.exists(season_file):

        return None


    season_df = pd.read_csv(
        season_file
    )


    season_df.columns = (
        season_df.columns
        .str.strip()
    )


    required_columns = [

        "Player",
        "Season",
        "Games",
        "Points",
        "Rebounds",
        "Assists",
        "Steals",
        "Blocks",
        "FG_Percentage"

    ]


    for column in required_columns:

        if column not in season_df.columns:

            season_df[column] = 0


    numeric_columns = [

        "Games",
        "Points",
        "Rebounds",
        "Assists",
        "Steals",
        "Blocks",
        "FG_Percentage"

    ]


    for column in numeric_columns:

        season_df[column] = pd.to_numeric(
            season_df[column],
            errors="coerce"
        ).fillna(0)


    season_df["Player"] = (
        season_df["Player"]
        .astype(str)
        .str.strip()
    )


    season_df["Season"] = (
        season_df["Season"]
        .astype(str)
        .str.strip()
    )


    season_df["PPG"] = 0.0

    season_df["RPG"] = 0.0

    season_df["APG"] = 0.0

    season_df["SPG"] = 0.0

    season_df["BPG"] = 0.0


    valid_games = (
        season_df["Games"] > 0
    )


    season_df.loc[
        valid_games,
        "PPG"
    ] = (
        season_df.loc[
            valid_games,
            "Points"
        ]
        /
        season_df.loc[
            valid_games,
            "Games"
        ]
    )


    season_df.loc[
        valid_games,
        "RPG"
    ] = (
        season_df.loc[
            valid_games,
            "Rebounds"
        ]
        /
        season_df.loc[
            valid_games,
            "Games"
        ]
    )


    season_df.loc[
        valid_games,
        "APG"
    ] = (
        season_df.loc[
            valid_games,
            "Assists"
        ]
        /
        season_df.loc[
            valid_games,
            "Games"
        ]
    )


    season_df.loc[
        valid_games,
        "SPG"
    ] = (
        season_df.loc[
            valid_games,
            "Steals"
        ]
        /
        season_df.loc[
            valid_games,
            "Games"
        ]
    )


    season_df.loc[
        valid_games,
        "BPG"
    ] = (
        season_df.loc[
            valid_games,
            "Blocks"
        ]
        /
        season_df.loc[
            valid_games,
            "Games"
        ]
    )


    for column in [

        "PPG",
        "RPG",
        "APG",
        "SPG",
        "BPG",
        "FG_Percentage"

    ]:

        season_df[column] = (
            season_df[column]
            .round(1)
        )


    return season_df


# ============================================================
# SEASON ANALYSIS
# ============================================================

@app.route("/season-analysis")
def season_analysis():

    season_df = prepare_season_dataframe()


    if season_df is None:

        return render_template(

            "season_analysis.html",

            players=[],

            seasons=[],

            selected_player="",

            selected_season="All",

            selected_record=None,

            best_season=None,

            comparison=None,

            season_data=[],

            error=(
                "nba_season_players.csv "
                "was not found."
            )

        )


    players = sorted(
        season_df["Player"]
        .dropna()
        .unique()
        .tolist()
    )


    selected_player = request.args.get(
        "player",
        ""
    ).strip()


    selected_season = request.args.get(
        "season",
        "All"
    ).strip()


    if (
        not selected_player
        or selected_player not in players
    ):

        selected_player = (
            players[0]
            if players
            else ""
        )


    player_df = season_df[
        season_df["Player"].str.lower()
        == selected_player.lower()
    ].copy()


    player_df = player_df.sort_values(
        by="Season"
    )


    seasons = (
        player_df["Season"]
        .dropna()
        .astype(str)
        .tolist()
    )


    if (
        selected_season != "All"
        and selected_season not in seasons
    ):

        selected_season = "All"


    # ========================================================
    # SELECTED RECORD
    # ========================================================

    selected_record = None


    if (
        selected_season != "All"
    ):

        selected_rows = player_df[
            player_df["Season"].astype(str)
            == str(selected_season)
        ]


        if not selected_rows.empty:

            selected_record = (
                selected_rows
                .iloc[0]
                .to_dict()
            )

    else:

        if not player_df.empty:

            selected_record = (
                player_df
                .iloc[-1]
                .to_dict()
            )


    # ========================================================
    # BEST SEASON
    # ========================================================

    best_season = None


    if not player_df.empty:

        best_index = player_df[
            "PPG"
        ].idxmax()


        best_season = (
            player_df
            .loc[best_index]
            .to_dict()
        )


    # ========================================================
    # SEASON COMPARISON
    # ========================================================

    comparison = {

        "best_ppg": None,

        "best_rpg": None,

        "best_apg": None,

        "best_fg": None

    }


    if not player_df.empty:

        best_ppg_index = (
            player_df["PPG"].idxmax()
        )

        best_rpg_index = (
            player_df["RPG"].idxmax()
        )

        best_apg_index = (
            player_df["APG"].idxmax()
        )

        best_fg_index = (
            player_df["FG_Percentage"].idxmax()
        )


        comparison["best_ppg"] = (
            player_df
            .loc[best_ppg_index]
            .to_dict()
        )


        comparison["best_rpg"] = (
            player_df
            .loc[best_rpg_index]
            .to_dict()
        )


        comparison["best_apg"] = (
            player_df
            .loc[best_apg_index]
            .to_dict()
        )


        comparison["best_fg"] = (
            player_df
            .loc[best_fg_index]
            .to_dict()
        )


    # ========================================================
    # TABLE DATA
    # ========================================================

    season_data = []


    for _, row in player_df.iterrows():

        season_data.append({

            "Season": str(
                row["Season"]
            ),

            "Games": int(
                row["Games"]
            ),

            "PPG": round(
                float(row["PPG"]),
                1
            ),

            "RPG": round(
                float(row["RPG"]),
                1
            ),

            "APG": round(
                float(row["APG"]),
                1
            ),

            "SPG": round(
                float(row["SPG"]),
                1
            ),

            "BPG": round(
                float(row["BPG"]),
                1
            ),

            "FG_Percentage": round(
                float(row["FG_Percentage"]),
                1
            )

        })


    return render_template(

        "season_analysis.html",

        players=players,

        seasons=seasons,

        selected_player=selected_player,

        selected_season=selected_season,

        selected_record=selected_record,

        best_season=best_season,

        comparison=comparison,

        season_data=season_data,

        error=None

    )


# ============================================================
# SEASON ANALYSIS API
# ============================================================

@app.route("/api/season-analysis-data")
def season_analysis_data():

    season_df = prepare_season_dataframe()


    if season_df is None:

        return []


    player_name = request.args.get(
        "player",
        ""
    ).strip()


    if player_name:

        season_df = season_df[
            season_df["Player"].str.lower()
            == player_name.lower()
        ].copy()


    if season_df.empty:

        return []


    season_df = season_df.sort_values(
        by="Season"
    )


    chart_data = []


    for _, row in season_df.iterrows():

        chart_data.append({

            "season": str(
                row["Season"]
            ),

            "games": int(
                row["Games"]
            ),

            "ppg": round(
                float(row["PPG"]),
                1
            ),

            "rpg": round(
                float(row["RPG"]),
                1
            ),

            "apg": round(
                float(row["APG"]),
                1
            ),

            "spg": round(
                float(row["SPG"]),
                1
            ),

            "bpg": round(
                float(row["BPG"]),
                1
            ),

            "fg": round(
                float(row["FG_Percentage"]),
                1
            )

        })


    return chart_data


# ============================================================
# RANKING
# ============================================================

@app.route("/ranking")
def ranking():

    ranking_df = (
        calculate_performance_ranking()
    )


    ranking_data = ranking_df[

        [

            "Rank",
            "Player",
            "Performance_Score",
            "Points",
            "Rebounds",
            "Assists",
            "Steals",
            "Blocks",
            "FG_Percentage",
            "TS_Percentage",
            "PER",
            "Win_Shares"

        ]

    ].to_dict("records")


    top_player = (
        ranking_data[0]
        if ranking_data
        else None
    )


    return render_template(

        "ranking.html",

        rankings=ranking_data,

        top_player=top_player

    )


# ============================================================
# LIVE NBA
# ============================================================

@app.route("/live")
def live():

    games = get_live_games()


    return render_template(

        "live.html",

        games=games

    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )