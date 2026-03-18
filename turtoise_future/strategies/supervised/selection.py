"""Feature selection using XGBoost"""

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import RandomizedSearchCV


def select_feature(market: str, direction: str = "long"):
    """
    Select best features for a market and direction.

    Args:
        market: Contract symbol
        direction: 'long' or 'short'

    Returns:
        Tuple of (optimized_parameters, recommended_feature_labels)
    """
    df = pd.read_csv(f"data/{market}.csv")
    df.set_index("Date", inplace=True)

    # Create target based on direction
    if direction == "long":
        df.loc[df["Close"].shift(-1) > df["Close"], "TARGET"] = 1
        df.loc[df["Close"].shift(-1) <= df["Close"], "TARGET"] = 0
    else:
        df.loc[df["Close"].shift(-1) < df["Close"], "TARGET"] = 1
        df.loc[df["Close"].shift(-1) >= df["Close"], "TARGET"] = 0

    df["TARGET"].fillna(0, inplace=True)

    # Remove unwanted columns
    df_tts = df.copy()
    df_tts.drop(columns=["Close", "Open", "High", "Low"], inplace=True)

    X = df_tts.iloc[:, :-1]
    y = df_tts.iloc[:, -1]

    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    classifier_0 = XGBClassifier(
        objective="binary:logistic",
        booster="gbtree",
        eval_metric="aucpr",
        subsample=0.8,
        colsample_bytree=1,
        random_state=1,
        use_label_encoder=False,
    )

    param_grid = {
        "gamma": [0, 0.1, 0.2, 0.5, 1, 1.5, 2, 3, 6, 12, 20],
        "learning_rate": [0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8],
        "max_depth": [1, 2, 3, 4, 5, 6, 8, 10],
        "n_estimators": [25, 50, 65, 80, 100, 115, 200],
    }

    grid_search = RandomizedSearchCV(
        estimator=classifier_0, param_distributions=param_grid, scoring="precision"
    )
    best_model = grid_search.fit(X_train, y_train)

    hyperparams = best_model.best_params_
    ne = hyperparams["n_estimators"]
    lr = hyperparams["learning_rate"]
    md = hyperparams["max_depth"]
    gm = hyperparams["gamma"]

    optimized_parameters = (ne, lr, md, gm)

    classifier_1 = XGBClassifier(
        objective="binary:logistic",
        booster="gbtree",
        eval_metric="aucpr",
        n_estimators=ne,
        learning_rate=lr,
        max_depth=md,
        gamma=gm,
        subsample=0.8,
        colsample_bytree=1,
        random_state=1,
        use_label_encoder=False,
    )

    eval_set = [(X_train, y_train)]
    classifier_1.fit(X_train, y_train, eval_set=eval_set, verbose=False)

    importance_features = classifier_1.feature_importances_
    mean_feature_importance = importance_features.mean()

    importance_labels = X.columns
    recommended_feature_labels = []
    for i, fi in enumerate(importance_features):
        if fi > mean_feature_importance:
            recommended_feature_labels.append(importance_labels[i])

    return (optimized_parameters, recommended_feature_labels)
