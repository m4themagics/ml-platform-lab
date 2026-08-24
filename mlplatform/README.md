# Shared platform layer

Planned home for the release contract, validation gates, immutable packaging interface,
rollout orchestration and evidence bundle creation.

Workload-specific schema and metrics enter through explicit adapters. If this layer branches
on a workload's business meaning, the abstraction has failed and must be redesigned before a
second path is copied.

## Why not `platform/`

The directory is named `mlplatform` because `platform` is a Python standard-library module. A
top-level package with that name shadows it for everything imported afterwards, including pandas
and scikit-learn, and the resulting import failure points nowhere near the cause.
