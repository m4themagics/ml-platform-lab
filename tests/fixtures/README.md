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
