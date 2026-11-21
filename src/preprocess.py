import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DROP_COLS = ["id", "label", "attack_cat"]
CAT_COLS = ["proto", "service", "state"]


def load_data(path):
    df = pd.read_csv(path)
    X = df.drop(columns=DROP_COLS)
    return X, df["label"], df["attack_cat"]


def build_preprocessor(X):
    num_cols = [c for c in X.columns if c not in CAT_COLS]
    return ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS),
        ("num", StandardScaler(), num_cols),
    ])