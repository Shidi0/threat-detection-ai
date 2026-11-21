from pathlib import Path
import joblib
import numpy as np

MODELS = Path(__file__).resolve().parent.parent / "models"
LOW, HIGH = 0.3, 0.6          # Normal < LOW <= Suspicious < HIGH <= Attack

_pre = joblib.load(MODELS / "preprocessor.joblib")
_rf = joblib.load(MODELS / "stage1_binary_rf.joblib")
_xgb = joblib.load(MODELS / "stage2_attack_xgb.joblib")
_le = joblib.load(MODELS / "attack_label_encoder.joblib")


def predict_flow(df_raw):
    """df_raw: DataFrame فيه الـ 42 Feature (من غير id و label و attack_cat)."""
    Xp = _pre.transform(df_raw)
    p = _rf.predict_proba(Xp)[:, 1]

    types, tconf = {}, {}
    idx = np.where(p >= LOW)[0]
    if len(idx):
        probs = _xgb.predict_proba(Xp[idx])
        for i, k, c in zip(idx, probs.argmax(1), probs.max(1)):
            types[i], tconf[i] = _le.classes_[k], round(float(c), 4)

    out = []
    for i, pa in enumerate(p):
        label = "Normal" if pa < LOW else "Suspicious" if pa < HIGH else "Attack"
        out.append({
            "prediction": label,
            "attack_type": types.get(i),
            "confidence": round(float(1 - pa if label == "Normal" else pa), 4),
            "attack_probability": round(float(pa), 4),
            "type_confidence": tconf.get(i),
        })
    return out