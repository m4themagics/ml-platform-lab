# Shared platform layer

Planned home for the release contract, validation gates, immutable packaging interface,
rollout orchestration and evidence bundle creation.

Workload-specific schema and metrics enter through explicit adapters. If this layer branches
on a workload's business meaning, the abstraction has failed and must be redesigned before a
second path is copied.
