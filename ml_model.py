import pandas as pd
import os

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# ============================================================
# DATA
# ============================================================

DATA_FILE = os.path.join(
    "data",
    "nba_players.csv"
)

df = pd.read_csv(DATA_FILE)


# ============================================================
# FEATURES AND TARGET
# ============================================================

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


# ============================================================
# DATA PREPARATION
# ============================================================

X = df[features]
y = df[target]


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


# ============================================================
# RANDOM FOREST MODEL
# ============================================================

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42
)

model.fit(
    X_train,
    y_train
)


# ============================================================
# MODEL EVALUATION
# ============================================================

predictions = model.predict(X_test)

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


# ============================================================
# FUNCTION FOR PLAYER PREDICTION
# ============================================================

def predict_player_win_shares(player_name):

    player_row = df[
        df["Player"].str.lower()
        == player_name.lower()
    ]

    if player_row.empty:
        return None

    player_features = player_row[
        features
    ]

    predicted_value = model.predict(
        player_features
    )[0]

    actual_value = player_row[
        target
    ].iloc[0]

    player_data = player_row.iloc[0].to_dict()

    player_data["difference"] = round(
        abs(actual_value - predicted_value),
        2
    )

    return {
        "predicted": round(predicted_value, 2),
        "actual": round(actual_value, 2),
        "difference": round(
            abs(actual_value - predicted_value),
            2
        ),
        "player_data": player_data
    }


# ============================================================
# MODEL INFORMATION
# ============================================================

def get_model_metrics():

    return {
        "mae": mae,
        "mse": mse,
        "r2": r2
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NBA PLAYER PERFORMANCE PREDICTION MODEL")
    print("=" * 60)

    print()
    print("Model: Random Forest Regressor")
    print()

    print(
        f"Mean Absolute Error: {mae:.2f}"
    )

    print(
        f"Mean Squared Error: {mse:.3f}"
    )

    print(
        f"R2 Score: {r2:.3f}"
    )

    print()

    sample_player = "Nikola Jokic"

    result = predict_player_win_shares(
        sample_player
    )

    if result:

        print(
            f"Player: {sample_player}"
        )

        print(
            f"Actual Win Shares: "
            f"{result['actual']:.2f}"
        )

        print(
            f"Predicted Win Shares: "
            f"{result['predicted']:.2f}"
        )

        print(
            f"Difference: "
            f"{result['difference']:.2f}"
        )

    print()
    print("=" * 60)

