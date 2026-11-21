# Module 1: Threat Detection & Classification

Models (not in Git): https://drive.google.com/file/d/1Q9IHHd1vkiI__VP6Ub26ZUJpg7m1_xCN/view?usp=sharing
Download `models.zip`, unzip it, and place the `models` folder next to `src`.
Two-stage detector trained on UNSW-NB15.

## Run

```
python src/train.py
```

Trains the models and saves them to `models/`.

## Use

```python
import sys
sys.path.insert(0, "src")
from predict import predict_flow

predict_flow(df)   # df = DataFrame with the 42 raw features
```

## Output (one dict per flow)

| field | meaning |
|---|---|
| prediction | Normal / Suspicious / Attack |
| attack_type | Generic, Exploits, Fuzzers, DoS, Reconnaissance, Analysis, Backdoor, Shellcode, Worms (None if Normal) |
| confidence | probability of the predicted label |
| attack_probability | Stage-1 probability that the flow is an attack |
| type_confidence | Stage-2 confidence in attack_type |

Bands on attack_probability: below 0.3 Normal, 0.3 to 0.6 Suspicious, 0.6 and above Attack.

## Results

- Validation (20% of train): FPR 1.0%, FNR 3.8%, Precision 99.2%.
- Official test set (175,341 flows, 68% attacks): FPR 1.34%, FNR 14.65%, Precision 99.3%, ROC-AUC 0.9835.

## Known limitations

- Fuzzers recall on the test set is only 20% (distribution shift). It accounts for about 83% of missed attacks.
- Analysis and Backdoor are hard to tell apart (similar features).
- The Suspicious band recovers about 37% of missed attacks, at the cost of about 3.9% of normal flows going to analyst review.
- Isolation Forest did not improve the hybrid (FPR 3.64% vs 1.93%), so it is not used for decisions.
