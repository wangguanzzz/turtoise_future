"""Model training and evaluation for supervised learning"""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score
from sklearn.metrics import precision_score
from ...config.commodities import COMMODITY_DICT
from ...config.settings import settings


def train_model(market: str, direction: str, params: tuple, features: list):
    """
    Train XGBoost classifier for a market and direction.

    Args:
        market: Contract symbol
        direction: 'long' or 'short'
        params: (n_estimators, learning_rate, max_depth, gamma)
        features: List of feature names to use

    Returns:
        Tuple of results
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
    features.append("TARGET")

    df_tts = df[features]
    X = df_tts.iloc[:, :-1]
    y = df_tts.iloc[:, -1]

    # Train/test split (time series based)
    train_size_rate = 0.7
    train_size = int(len(X) * train_size_rate)
    test_size = len(X) - train_size

    X_train = X.head(train_size)
    y_train = y.head(train_size)
    X_test = X.tail(test_size)
    y_test = y.tail(test_size)

    ne, lr, md, gm = params

    classifier = XGBClassifier(
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

    eval_set = [(X_train, y_train), (X_test, y_test)]
    classifier.fit(X_train, y_train, eval_set=eval_set, verbose=False)

    train_yhat = classifier.predict(X_train)
    test_yhat = classifier.predict(X_test)

    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=1, random_state=1)
    train_results = cross_val_score(
        classifier, X_train, y_train, scoring="precision", cv=cv, n_jobs=-1
    )
    test_results = cross_val_score(
        classifier, X_test, y_test, scoring="precision", cv=cv, n_jobs=-1
    )

    train_precision = round(precision_score(y_train, train_yhat, average=None)[1], 3)
    train_sdev = round(train_results.std(), 2)
    test_precision = round(precision_score(y_test, test_yhat, average=None)[1], 3)
    test_sdev = round(test_results.std(), 2)

    print(f"TRAIN: {market}, {direction}")
    print("Average Precision K-Fold", round(train_results.mean(), 2))
    print(f"TEST: {market}, {direction}")
    print("Average Precision K-Fold", round(test_results.mean(), 2))

    # Get prediction for latest data
    X_predict = X.tail(1)
    y_predict = classifier.predict(X_predict)
    last_date = X_predict.index[0]
    last_close = df["Close"][last_date]
    signal = y_predict[0]

    market_name, size = COMMODITY_DICT[market]
    trade_size = int(settings.one_percent_threshold / (last_close * size * 0.01))

    return (
        market,
        market_name,
        test_precision,
        test_sdev,
        train_precision,
        train_sdev,
        last_date,
        params,
        trade_size,
        signal,
    )
