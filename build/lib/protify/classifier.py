
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def train_classifier(df):
    features = ['prot', 'snr', 'power', 'mpower', 'func', 'gmag']
    df_ = df.dropna(subset=features + ['rotate?'])
    X = df_[features]
    y = df_['rotate?']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    model = RandomForestClassifier(n_estimators=450, max_depth=15)
    model.fit(X_train, y_train)
    accuracy = accuracy_score(y_test, model.predict(X_test))
    return model, accuracy

def apply_classifier(model, summary_df):
    features = ['prot', 'snr', 'power', 'mpower', 'func', 'gmag']
    X = summary_df[features].copy()
    summary_df['rotate?'] = model.predict(X)
    return summary_df
