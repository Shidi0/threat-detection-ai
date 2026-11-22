# Module 1 Report: Threat Detection & Classification

## Overview

Module 1 labels each network flow Normal, Suspicious or Attack and names the attack type, with a 1.34% false-positive rate on the official UNSW-NB15 test set (175,341 flows).

It is a two-stage model: a Random Forest decides attack vs. normal, then an XGBoost model names the attack type. Precision on the test set is 99.3%, but 14.65% of attacks are missed, almost all of them Fuzzers (see Limitations).

Code and README: [github.com/Shidi0/threat-detection-ai](https://github.com/Shidi0/threat-detection-ai).

## Dataset comparison

We chose UNSW-NB15 because it ships with a ready Train/Test split, has 10 classes with severe imbalance, and is lighter to run than CIC-IDS2017.

| | UNSW-NB15 | CIC-IDS2017 |
| --- | --- | --- |
| Origin | UNSW Canberra; traffic generated with the IXIA PerfectStorm tool in a lab | Canadian Institute for Cybersecurity (UNB); 5-day capture, 3 to 7 July 2017 |
| Features | 49 plus a label | 80+ (85 in one survey) |
| Attack types | 9 categories: Fuzzers, Analysis, Backdoors, DoS, Exploits, Generic, Reconnaissance, Shellcode, Worms | Brute Force, DoS, DDoS, Heartbleed, Web Attacks, Infiltration, Botnet, Port Scan (21 specific attacks in the survey) |
| Size | 2,540,044 records in 4 CSV files | About 51 GB of raw PCAP; labelled CSVs per day; flow count not stated on the official page |
| Benign share | About 87% in the full data; 44.9% in our train file, 31.9% in our test file | About 72% (survey figure) |
| ML-ready split | Yes, Train/Test provided | No official split; must be built without leakage |

Sources: [UNSW-NB15 page](https://research.unsw.edu.au/projects/unsw-nb15-dataset), [CIC-IDS2017 page](https://www.unb.ca/cic/datasets/ids-2017.html), [Benchmarking the Benchmark (survey)](https://arxiv.org/pdf/2104.09029).

**File-naming caveat.** The UNSW page describes the training set as 175,341 records and the testing set as 82,332. The downloadable files named `training-set` and `testing-set` are the reverse (82,332 and 175,341). We followed the file names: trained on the 82,332-row file and evaluated on the 175,341-row file.

Both datasets are synthetic lab traffic, so results may not carry over to a real network. We did not run CIC-IDS2017; cross-dataset evaluation is future work.

## Pipeline

The pipeline fits every transformation on the training split only, so no information leaks from validation or test data.

1. **Clean and select features.** The train file has no missing values and no duplicates. We drop `id` and the two targets, leaving 42 features.
2. **Split.** 80/20 Train/Validation (65,865 / 16,467 flows), stratified by attack category so rare classes appear in both.
3. **Encode and scale.** One-hot encoding for `proto`, `service` and `state` (131, 13 and 7 values), and standard scaling for the 39 numeric features: 190 columns in total. Unseen categories are ignored instead of raising an error.
4. **Stage 1, attack vs. normal.** A Random Forest (200 trees) outputs an attack probability.
5. **Stage 2, attack type.** An XGBoost model trained on attack flows only, with square-root class weights, names one of 9 attack types.
6. **Decision bands on the Stage 1 probability.** Below 0.3 is Normal, 0.3 to 0.6 is Suspicious (sent to an analyst), and 0.6 or above is Attack.

The 0.6 threshold was chosen on the validation set. At 0.5 the false-positive rate was 2.0% and 2.5% of attacks were missed; at 0.6 it is 1.0% and 3.8%. Going higher cost more missed attacks than it saved in false alarms (5.6% missed at 0.7).

## Results

On the validation set the final Random Forest at threshold 0.6 has the lowest false-positive rate (1.0%) with precision 0.992; on the official test set the false-positive rate is 1.34% and 14.65% of attacks are missed.

**Validation set (16,467 flows), attack = positive class**

| Model | Precision | Recall | F1 | ROC-AUC | FPR | FNR | ms/sample |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Logistic Regression (baseline) | 0.928 | 0.919 | 0.924 | 0.977 | 8.69% | 8.07% | 0.00076 |
| Random Forest, threshold 0.5 | 0.984 | 0.975 | 0.979 | 0.997 | 2.00% | 2.54% | 0.00833 |
| **Random Forest, threshold 0.6 (final)** | **0.992** | 0.962 | 0.977 | 0.997 | **1.00%** | 3.81% | 0.00638 |
| XGBoost, threshold 0.5 | 0.987 | 0.975 | 0.981 | 0.998 | 1.55% | 2.55% | 0.00158 |
| Isolation Forest | 0.947 | 0.249 | 0.394 | 0.734 | 1.70% | 75.12% | - |
| Hybrid (Random Forest or Isolation Forest) | 0.970 | 0.974 | 0.972 | - | 3.64% | 2.56% | - |

XGBoost was evaluated at the default 0.5 without threshold tuning, so its comparison with the tuned Random Forest is not like for like. Timings are rough per-sample estimates.

**Official test set (175,341 flows, 68% attacks), final model, evaluated once**

| Precision | Recall | FPR | FNR | ROC-AUC | Accuracy |
| --- | --- | --- | --- | --- | --- |
| 0.993 | 0.853 | 1.34% | 14.65% | 0.9835 | 89.6% |

The Suspicious band (0.3 to 0.6) catches 6,505 of the 17,484 attacks missed at 0.6, which lowers the effective miss rate to about 9.2%. The cost is 2,212 normal flows (3.9% of normal traffic) sent to analyst review.

For attack-type naming on the validation set, the two-stage model reaches a macro F1 of 0.633 (the single-stage baseline was 0.613).

Reproduce the test-set numbers with `python src/evaluate.py`.

## Limitations and future work

The model misses most Fuzzers on the test set: only 20.3% are detected, and Fuzzers account for about 83% of all missed attacks. Detection of the other attack types on the test set is between 72.6% (Analysis) and 99.8% (Generic).

- **Distribution shift.** Fuzzers recall on the validation set is 81%, so validation did not reveal the problem. The test set has more Fuzzers (18,184 vs. 6,062 in train) and a different mix of attacks (68% vs. 55% attacks). Re-weighting Fuzzers on validation gave only small gains (recall 0.81 to 0.86) and raised the false-positive rate from 1.0% to 1.5%, so we kept the original model rather than tune against the test set.
- **Analysis and Backdoor look alike.** In attack-type naming, 68% of Analysis flows were labelled Backdoor and 58% of Backdoor flows were labelled Analysis. Merging them lifts validation macro F1 from 0.633 to 0.73, but that figure is not comparable because it removes the hardest confusion by definition. Module 3 can treat both with the same action (analyst review).
- **Worms** has only 9 validation samples, so its scores are unreliable.
- **Isolation Forest** did not help. Used alone it misses 75% of attacks; combined with the Random Forest it doubled false positives (3.64% vs. 1.93%) with no gain in detection. It is not used for decisions. Its anomaly score could still feed Module 2, and its value on unseen (zero-day) attacks is untested.
- **Single dataset.** Results come from one lab-generated dataset. Testing on CIC-IDS2017 would show how well the model carries over.

Future work: threshold tuning for XGBoost, features less tied to specific attack tools, a zero-day experiment with Isolation Forest, and cross-dataset evaluation.
