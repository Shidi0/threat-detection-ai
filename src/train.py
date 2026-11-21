from pathlib import Path
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

from preprocess import load_data, build_preprocessor

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
MODELS.mkdir(exist_ok=True)

X, y_bin, y_multi = load_data(ROOT / "data" / "UNSW_NB15_training-set.csv")

X_tr, X_val, ybt, ybv, ymt, ymv = train_test_split(
    X, y_bin, y_multi, test_size=0.2, stratify=y_multi, random_state=42)

pre = build_preprocessor(X_tr)
Xtr_p = pre.fit_transform(X_tr)      # fit على الـ Train بس
Xval_p = pre.transform(X_val)

# المرحلة 1: طبيعي vs هجوم
rf = RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=42)
rf.fit(Xtr_p, ybt)

# المرحلة 2: نوع الهجوم (على الهجمات بس، بأوزان sqrt)
atk = (ybt == 1).values
le_atk = LabelEncoder().fit(ymt[atk])
y_a = le_atk.transform(ymt[atk])
w = compute_sample_weight("balanced", y_a) ** 0.5
xgb = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1,
                    n_jobs=-1, random_state=42, eval_metric="mlogloss")
xgb.fit(Xtr_p[atk], y_a, sample_weight=w)

joblib.dump(pre, MODELS / "preprocessor.joblib")
joblib.dump(rf, MODELS / "stage1_binary_rf.joblib")
joblib.dump(xgb, MODELS / "stage2_attack_xgb.joblib")
joblib.dump(le_atk, MODELS / "attack_label_encoder.joblib")

p = rf.predict_proba(Xval_p)[:, 1]
print(classification_report(ybv, (p >= 0.6).astype(int), digits=3))
print("Saved models to", MODELS)