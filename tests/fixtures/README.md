# Failure fixtures

Small, inspectable releases used to falsify platform guarantees:

- schema-incompatible model;
- missing or checksum-invalid model artifact;
- crash-looping image;
- readiness failure;
- deterministic latency regression;
- resource-pressure workload.

Fixtures are added with the phase that exercises them and must traverse the normal release
path. A hidden test-only bypass does not prove production behaviour.

## What exists now

Nothing is stored as a file yet. The schema-incompatible cases for workload 1 are built in-test
from `services.fraud_scoring.data.synthetic_frame`, which is seeded and therefore reproducible
without committing data or depending on a download. See `tests/test_fraud_contract.py`.

A fixture becomes a file here once it has to survive outside a test process -- a broken artifact
loaded by a running service, or a bad image pulled by a rollout. That starts at M2.
