# Workload 1 — fraud scoring

Card-transaction fraud scoring. Chosen because the operational story is real: the answer is
needed inside a payment authorisation, so latency has a hard ceiling, and a model that quietly
stops catching fraud costs money while every dashboard stays green. That is the exact failure
this repository claims to detect and reverse.

The model itself is not the point and is meant to stay boring.

## Data

| | |
|---|---|
| Source | OpenML dataset `42175` (`CreditCardFraudDetection`), <https://www.openml.org/d/42175> |
| Origin | Worldline and the ULB Machine Learning Group, anonymised European card transactions, September 2013 |
| Licence | Open Database License (ODbL) v1.0 |
| Shape | 284,807 transactions, 492 fraudulent (0.172%) |
| Committed? | No. `data/` is ignored; only the fingerprint is committed |

Features `V1`–`V28` are PCA components published in place of the original fields; `Amount` and
the target `Class` are original. `Time` is seconds since the first transaction in the file. It
orders the split and is never a feature — it encodes when collection happened, not what fraud
looks like.

Not dataset `1597`, which holds the same transactions. There `Time` is flagged as a row
identifier, so scikit-learn drops it without complaint and the frame arrives with 30 columns
instead of 31 — which would have turned the time-ordered split below into a positional one that
merely looked correct.

Synthetic rows (`synthetic_frame`) exist for contract tests and, later, for load traffic. They
never train a released model.

## Contract

- **Schema version** `fraud_scoring.v1`, declared in `contract.py` and stored inside the artifact.
- **Input**: exactly the 29 features in contract order, numeric, finite, `Amount >= 0`. Unknown
  columns are rejected rather than ignored.
- **Output**: `P(fraud)` in `[0, 1]`, plus the decision at a stated threshold.
- **Incompatible** — rejected before traffic: a different schema version, a missing or unknown
  feature, or the same features in a different order.
- **Worse** — a quality question, caught by the metric gate: average precision below threshold.

The decision threshold is still provisional. It has to be read off the precision/recall curve and
written into `configs/platform.toml` before the first measured run.

## Metric

Average precision on a time-ordered holdout. Accuracy is useless at a 0.172% base rate — always
answering "legitimate" scores 99.8% — and ROC AUC stays flattering because the true-negative pool
is enormous. Average precision is what actually drops when the model stops finding fraud.

## Split

Time-ordered, last 20% held out, with the cut pushed forward to the next distinct timestamp so no
single second lands on both sides. A shuffled split would let the model see the later half of a
fraud campaign it is being scored on.

## Run

```bash
make data     # download once, canonicalise, write the fingerprint
make train    # deterministic fit, artifact, metrics, release record
```

`make data` fetches ~150 MB on first run and caches it under `data/raw/`. Everything else,
including the whole test suite, runs offline.

## Measured baseline

Reproduced on 2026-08-24, `make data && make train`, laptop CPU, about five seconds.

| | |
|---|---|
| Dataset `content_hash` | `0734105a153fe42b683d3f6bfc73471598e7ac6ec98408107a440df1b507fc86` |
| Dataset `schema_hash` | `95534149b07ba559a32c3ebc3753956a8af82e01f44d51a8c2950214893c8f32` |
| Rows | 227,845 train / 56,962 holdout |
| Positives | 417 train (0.183%) / 75 holdout (0.132%) |
| Average precision | **0.801** |
| Artifact `sha256` | `109c3ca7520cfbbc2e57dfb11e4d68646b2271444cfd6081af460f4dc160a9d1` |

Two independent runs produced the same artifact checksum, which is the property the release
record depends on.

The positive rate is lower in the holdout than in training. That is the time split doing its job:
the fraud rate genuinely moves across the two days, and a shuffled split would have hidden it.

This is a training result. It says nothing about latency, availability or recovery.

## Not here yet

No HTTP service, container, MLflow run or registered model version. Those arrive with M2 and
phase 2. The release record currently identifies a release by commit, dataset fingerprint and
artifact checksum, which is the honest subset of the chain in `docs/architecture.md`.
