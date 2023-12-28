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


# General Metrics
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import precision_score
from sklearn.metrics import confusion_matrix
import pickle
from constants import COMMODITY_DICT


def binary_classification(market,direction,params,features):
    # Data Extraction
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
    
    # Fill NA
    df["TARGET"].fillna(0, inplace=True)
    
    features.append("TARGET")
    # Feature Selection
    df_tts = df.copy()
    
    # Feature Selection
    df_tts = df.copy()
    df_tts = df_tts[features]
    
    # Split into X and Y Data
    X = df_tts.iloc[:, : -1]
    y = df_tts.iloc[:, -1]
    
    # Perform Train Test Split (Timeseries based method)
    train_size_rate = 0.7
    train_size = int(len(X) * train_size_rate)
    test_size = len(X) - train_size

    X_train = X.head(train_size)
    y_train = y.head(train_size)
    X_test = X.tail(test_size)
    y_test = y.tail(test_size)

    size_check = len(y_test) + len(y_train) == len(X)
    print("Shape of X_train: ", X_train.shape)
    print("Shape of y_train: ", y_train.shape)
    print("Shape of X_test: ", X_test.shape)
    print("Shape of y_test: ", y_test.shape)
    print("Size Matches: ", size_check)

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
    ne,lr,md,gm = params
    
    # XGBOOST Classifier
    classifier = XGBClassifier(
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
    # Set parameters
    classifier.set_params(eval_metric=eval_metric_list)
    eval_set = [(X_train, y_train), (X_test, y_test)]
    classifier.fit(X_train, y_train, 
                eval_set=eval_set, 
                verbose=False)
    # Save the model to a file
    # with open(f"model/{market}_{direction}.pkl", "wb") as file:
    #     pickle.dump(classifier, file)
    
    # Load the model from the file
    # with open("xgb_classifier_model.pkl", "rb") as file:
    #     loaded_classifier = pickle.load(file)
    
    # Get Predictions Training
    train_yhat = classifier.predict(X_train)
    # train_yhat_proba = classifier.predict_proba(X_train)
    
    # Get Predictions Test
    test_yhat = classifier.predict(X_test)
    # test_yhat_proba = classifier.predict_proba(X_test)
    # Set K-Fold Cross Validation Levels
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=1, random_state=1)
    # Training and Test Results
    train_results = cross_val_score(classifier, X_train, y_train, scoring=scoring, cv=cv, n_jobs=-1)
    test_results = cross_val_score(classifier, X_test, y_test, scoring=scoring, cv=cv, n_jobs=-1)
    
    
    # Comparison of Results
    train_precision = round(precision_score(y_train, train_yhat, average=None)[1], 3)
    train_sdev = round(train_results.std(), 2)
    test_precision = round(precision_score(y_test, test_yhat, average=None)[1], 3)
    test_sdev = round(test_results.std(), 2)
    print(f"TRAIN: {market},{direction}")
    print("Average Acc K-Fold", round(train_results.mean(), 2))
    print("Std Dev K-Fold", train_sdev)
    print("Precision Score 0", round(precision_score(y_train, train_yhat, average=None)[0], 3))
    print("Precision Score 1", train_precision)
    print("----- ----- ----- ----- ----- ----- -----")
    print(f"TEST: {market},{direction}")
    print("Average Acc K-Fold", round(test_results.mean(), 2))
    print("Std Dev K-Fold", test_sdev)
    print("Precision Score 0", round(precision_score(y_test, test_yhat, average=None)[0], 3))
    print("Precision Score 1", test_precision )
    print("")
    
    # get real predicted last price
    X_predict = X.tail(1)
    y_predict = classifier.predict(X_predict)
    last_date = X_predict.index[0]
    signal = y_predict[0]
    market_name,size = COMMODITY_DICT[market]
    
    return (market,market_name,test_precision, test_sdev,train_precision,train_sdev,last_date,params,signal)