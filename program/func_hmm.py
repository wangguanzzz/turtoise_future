from hmmlearn import hmm
import numpy as np

def add_hmm_feature(data):
    X_train = data[["Returns", "Range"]].copy()
    model = hmm.GaussianHMM(n_components=4, covariance_type='full',  n_iter=500)
    model.fit(np.array(X_train.values))
    
    hidden_states = model.predict(np.array(X_train.values))
    data['HMM'] = hidden_states
    
    return data
