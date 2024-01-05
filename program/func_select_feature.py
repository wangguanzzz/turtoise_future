# Remove Future Warnings
# import warnings
# warnings.simplefilter(action='ignore', category=FutureWarning)

# General
import numpy as np

# Data Management
import pandas as pd
from sklearn.model_selection import train_test_split

# Machine Learning
from xgboost import XGBClassifier
from sklearn.model_selection import RandomizedSearchCV, cross_val_score
from sklearn.model_selection import RepeatedStratifiedKFold

# Evaluation
from sklearn.metrics import precision_score


def select_feature(market, direction='long'):
    df = pd.read_csv(f"data/{market}.csv")
    df.set_index("Date", inplace=True)
    
    # Specify Target
    # if direction == 'long':
    #     df.loc[df["Range"].shift(-1) > df["Avg_Range"], "TARGET"] = 1
    #     df.loc[df["Range"].shift(-1) <= df["Avg_Range"], "TARGET"] = 0
    # else:
    #     df.loc[df["Range"].shift(-1) < df["Avg_Range"], "TARGET"] = 1
    #     df.loc[df["Range"].shift(-1) >= df["Avg_Range"], "TARGET"] = 0
    if direction == 'long':
        df.loc[df["Close"].shift(-1) > df["Close"],'TARGET' ] =1
        df.loc[df["Close"].shift(-1) <= df["Close"],'TARGET' ] =0
    else:
        df.loc[df["Close"].shift(-1) < df["Close"],'TARGET' ] =1
        df.loc[df["Close"].shift(-1) >= df["Close"],'TARGET' ] =0
    # Check for NaNs
    nan_location = np.where(np.isnan(df))
    nan_location
    # Fill NA
    df["TARGET"].fillna(0, inplace=True)
    # Remove unwanted columns
    df_tts = df.copy()
    df_tts.drop(columns=["Close", "Open", "High", "Low"], inplace=True)
    # Split into Learning (X) and Target (y) Data
    X = df_tts.iloc[:, : -1]
    y = df_tts.iloc[:, -1]
    # Perform Train Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    # Select type of model to optimize for
    is_binary = True
    is_optimise_for_precision = True
    # Determine Objective and Eval Metrics
    if is_binary:
        objective = "binary:logistic"
        eval_metric = "logloss"
        eval_metric_list = ["error", "logloss", eval_metric]
    else:
        objective = "multi:softmax"
        eval_metric = "mlogloss"
        eval_metric_list = ["merror", "mlogloss", eval_metric]
    # Refine Eval Metric
    if is_binary and is_optimise_for_precision:
        eval_metric = "aucpr"
        scoring = "precision"
    elif is_binary and not is_optimise_for_precision:
        eval_metric = "auc"
        scoring = "f1"
    else:
        scoring = "accuracy"
    # Build First Classifier Model 0
    classifier_0 = XGBClassifier(
        objective=objective,
        booster="gbtree",
        eval_metric=eval_metric,
        subsample=0.8,
        colsample_bytree=1,
        random_state=1,
        use_label_encoder=False
    )
    # Provide Gris for Hyperparams
    param_grid = {
        "gamma": [0, 0.1, 0.2, 0.5, 1, 1.5, 2, 3, 6, 12, 20],
        "learning_rate": [0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8],
        "max_depth": [1, 2, 3, 4, 5, 6, 8, 10],
        "n_estimators": [25, 50, 65, 80, 100, 115, 200]
    }
    # Perform Random Search for Best Hyper params
    grid_search = RandomizedSearchCV(estimator=classifier_0, param_distributions=param_grid, scoring=scoring)
    best_model = grid_search.fit(X_train, y_train)
    hyperparams = best_model.best_params_
    ne = hyperparams["n_estimators"]
    lr = hyperparams["learning_rate"]
    md = hyperparams["max_depth"]
    gm = hyperparams["gamma"]
    # output optimized_parameters
    optimized_parameters = (ne,lr,md,gm)
    # Build Classification Model 1
    classifier_1 = XGBClassifier(
        objective=objective,
        booster="gbtree",
        eval_metric=eval_metric,
        n_estimators=ne,
        learning_rate=lr,
        max_depth=md,
        gamma=gm,
        subsample=0.8,
        colsample_bytree=1,
        random_state=1,
        use_label_encoder=False
    )
    # Fit Model
    classifier_1.set_params(eval_metric=eval_metric_list)
    eval_set = [(X_train, y_train)]
    classifier_1.fit(
        X_train,
        y_train,
        eval_set=eval_set,
        verbose=False
    )
    importance_features = classifier_1.feature_importances_
    # Select Best Features
    mean_feature_importance = importance_features.mean()
    i = 0
    # output
    importance_labels = X.columns
    recommended_feature_labels = []
    for fi in importance_features:
        if fi > mean_feature_importance:
            recommended_feature_labels.append(importance_labels[i])
        i += 1
    return (optimized_parameters, recommended_feature_labels)
