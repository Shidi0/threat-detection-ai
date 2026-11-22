from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score)

from preprocess import load_data
from predict import _pre, _rf

ROOT = Path(__file__).resolve().parent.parent
THRESHOLD = 0.6      # chosen on the validation set
LOW = 0.3            # lower edge of the Suspicious band

X, y_bin, y_multi = load_data(ROOT / "data" / "UNSW_NB15_testing-set.csv")
p = _rf.predict_proba(_pre.transform(X))[:, 1]
pred = (p >= THRESHOLD).astype(int)

tn, fp, fn, tp = confusion_matrix(y_bin, pred).ravel()
print(classification_report(y_bin, pred, digits=3))
print("FPR:", round(fp / (fp + tn), 4), "| FNR:", round(fn / (fn + tp), 4))
print("ROC-AUC:", round(roc_auc_score(y_bin, p), 4))

sus = (p >= LOW) & (p < THRESHOLD)
print("Attacks missed at threshold:", int(((y_bin == 1) & (pred == 0)).sum()))
print("  of them in Suspicious band:", int(((y_bin == 1) & sus).sum()))
print("Normal flows in Suspicious band:", int(((y_bin == 0) & sus).sum()))

atk = y_multi != "Normal"
rate = pd.Series(pred[atk.values]).groupby(y_multi[atk].values).mean()
print("\nDetection rate per attack type:")
print(rate.sort_values().round(3))