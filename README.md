# ML Platform Lab

> **Portfolio status: active as of 2026-08-24.** The current deliverable is a
> **minimum operational surface** — probes, rollout, resource sizing and p95/p99 evidence by the
> shortest path through the phases below — not the full twelve-week Must. Nothing is deployed
> yet; the table under [Status](#status) is the executable state, and it changes only when a
> command works from a clean checkout.

[![python](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![kubernetes](https://img.shields.io/badge/Kubernetes-planned-326CE5?logo=kubernetes&logoColor=white)](docs/development-plan.md)
[![terraform](https://img.shields.io/badge/Terraform-planned-844FBA?logo=terraform&logoColor=white)](docs/development-plan.md)

A production-like path from a trained model to an observable, recoverable Kubernetes
service. The model is deliberately small; the engineering result is the release system
around it.

> **Flagship question.** Can one reusable release path move a validated model from commit to
> an immutable Kubernetes deployment and reject or roll back bad releases before the measured
> service objective is exhausted?

This is not a catalogue of tools. MLflow, Kubernetes, Terraform, OpenTelemetry and the cloud
exist here only when they close a specific lifecycle or failure-mode gap. The result is a
release/recovery matrix with timings and immutable identifiers, not a screenshot of a green
dashboard.

```mermaid
flowchart LR
    C["Code + data revision"] --> T["Train and evaluate"]
    T --> M["MLflow run + registered version"]
    M --> G{"Quality and contract gates"}
    G -->|pass| I["OCI image<br/>model version + image digest pinned"]
    G -->|fail| X["Rejected release"]
    I --> R["Kubernetes rollout"]
    R --> S["Inference service"]
    S --> O["Metrics + traces + logs"]
    O --> A{"SLO / canary analysis"}
    A -->|healthy| P["Promote"]
    A -->|regression| B["Automatic rollback"]
```

## What must be demonstrated

| Claim | Required evidence |
|---|---|
| Reproducible lifecycle | commit, data fingerprint, MLflow run/model version and image digest are linked |
| Safe release | an incompatible or regressed candidate is rejected before full traffic |
| Reliable serving | probes, requests/limits, autoscaling and rollout behaviour are tested under declared load |
| Observable operation | p50/p95/p99, error rate, saturation and model version are queryable; one request is traceable |
| Recovery | repeated failure drills report detection and recovery timestamps, not just a successful final state |
| Reusable platform path | a second model workload uses the same contract and deployment template without copied pipeline logic |
| Reproducible cloud | Terraform can create, smoke-test and destroy the AWS environment without console steps |

The project will not claim a monthly production SLA from a short benchmark. It reports a
bounded load-test objective and exactly how long that observation lasted.

## Status

**Active. Phase 0 is closed as scaffold and preregistration; no platform workload is deployed
yet.** There is no Kubernetes cluster, cloud infrastructure, MLflow result, latency number or
reliability result in this repository today. The current files define scope, evidence and the
order of work; scaffold tests make unset decisions visible. `configs/platform.toml` still reads
`status = "scaffold"` on purpose — reviving the plan does not change executable state.

Work now runs on the shortest path to a minimum operational surface (M1–M4 in the
[development plan](docs/development-plan.md#возврат-minimum-operational-surface)); phases 2 and
6–9 are deferred until that surface holds.

| Phase | Deliverable | State |
|---:|---|---|
| 0 | Architecture, learning contract, cost and reliability gates | scaffolded |
| 1 | Small workload, data/model contract, deterministic evaluation | not started — trimmed into M1 |
| 2 | MLflow tracking, registry and lineage | not started — deferred past the surface |
| 3 | Immutable inference image and local service benchmark | not started — trimmed into M2 |
| 4 | Local Kubernetes deployment: probes, resources, HPA | not started — **M3, the core of the surface** |
| 5 | OpenTelemetry + Prometheus/Grafana and declared SLO | not started — RED slice is M4, rest deferred |
| 6 | Candidate rollout, automated analysis and rollback | not started — deferred past the surface |
| 7 | AWS infrastructure through Terraform and GitHub OIDC | not started — deferred past the surface |
| 8 | Second workload through the same golden path | not started — deferred past the surface |
| 9 | Clean-checkout reproduction and failure report | not started — deferred past the surface |

The twelve-week Must scope ends at phase 9. Kafka is a post-Must extension and opens only
with an actual asynchronous audit path, idempotent consumption, retries and a consumer-lag
drill. A producer and consumer with no failure contract do not count.

## Results

Empty until the [reliability protocol](docs/reliability-protocol.md) passes. Thresholds are
set before the first measured run and stay beside the load profile.

| Scenario | Candidate outcome | Availability | p95 / p99 | Detection time | Recovery time | Evidence |
|---|---|---:|---:|---:|---:|---|
| Healthy release | — | — | — | n/a | n/a | — |
| Schema-incompatible model | — | — | — | — | — | — |
| Crash-looping image | — | — | — | — | — | — |
| Latency regression | — | — | — | — | — | — |
| Registry unavailable during rollout | — | — | — | — | — | — |

No row is filled from a one-off manual demonstration. Raw load-generator output, Prometheus
queries, rollout events and immutable release identifiers are retained for every row.

## Scope boundaries

- One deliberately simple CPU model first; this is not a modelling competition.
- Local-first with Docker and `kind`; AWS is added only after the lifecycle and drills work
  locally.
- The deployed manifest pins an exact model version and image digest. An MLflow alias may
  select a candidate during promotion, but it is resolved before deployment.
- Native Kubernetes rollout behaviour is learned before adding rollout automation.
- No feature store, custom orchestrator, service mesh, multi-region design, GPU serving or
  distributed training in Must.
- No static AWS keys. CI authentication is short-lived and role-based.
- No cloud apply until spend limits, ownership tags and the destroy path are explicit.

## Planned layout

```text
services/           tiny training and inference workloads
platform/           shared model contract, release gates and deployment tooling
infra/              local Kubernetes and Terraform-owned AWS infrastructure
configs/            explicit platform decisions and preregistered thresholds
experiments/        release and recovery drills
reports/            reviewed results; raw run payloads stay untracked
tests/fixtures/      small incompatible and regressed release fixtures
docs/                architecture, plan, protocol, ADRs and learning tracks
```

Directories are intentionally populated only when their phase begins. Planned components are
not presented as implemented ones.

## Reproduce the current scaffold

```bash
make install
make check
```

Later phases add separate commands for local bootstrap, training, deployment, drills and cloud
destruction. A command enters this section only after it works from a clean checkout.

## Documents

- [Development plan](docs/development-plan.md) — twelve-week Must path and stop conditions.
- [Architecture](docs/architecture.md) — planned boundaries, identifiers and failure model.
- [Reliability protocol](docs/reliability-protocol.md) — what a benchmark or recovery claim
  must contain.
- [Learning track](docs/learning-tracks/platform-engineering.md) — the order in which the
  underlying skills are learned.
- [Learning contract](LEARNING.md) — where AI assistance stops and author ownership begins.
