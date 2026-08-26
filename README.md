# ML Platform Lab

> **Portfolio status: PAUSED after M1, as of 2026-08-26.** M1 remains executable
> evidence; M2–M4 are retained backlog.

[![python](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![kubernetes](https://img.shields.io/badge/Kubernetes-M3%20planned-326CE5?logo=kubernetes&logoColor=white)](docs/development-plan.md)

A deliberately small model workload used to learn and prove release identity, immutable
packaging, Kubernetes operational semantics and service-side measurements. Status follows
executable evidence, not diagrams or tool names.

## Retained question

If the project resumes, can one small model move from a reproducible training result to an immutable local service
whose probes, rollout, resources, autoscaling and RED behaviour are measured and explained?

The answer is bounded to four milestones:

| Milestone | Hours | Required result | State |
|---|---:|---|---|
| M1 | 6 | workload, data/model contract, deterministic training and release identity | **done** |
| M2 | 8 | immutable image, golden and malformed requests, graceful shutdown, local load baseline | paused · not started |
| M3 | 14 | `kind` deployment, startup/readiness/liveness, requests/limits, rollout, PDB and HPA | paused · not started |
| M4 | 6 | RED, in-flight and saturation metrics plus p95/p99 under a declared load profile | paused · not started |

M1–M4 total 34 hours. With M1 closed, **28 hours remain**.

## Executable status

**Nothing is served or deployed yet.** There is no HTTP service, image, local cluster,
latency result, availability result, MLflow run or cloud resource today.

What does run from a clean checkout:

| Evidence | Current fact |
|---|---|
| Workload | [`fraud_scoring`](services/fraud_scoring/README.md): 284,807 transactions, 492 fraudulent |
| Dataset identity | `content_hash` `0734105a…`, `schema_hash` `95534149…` |
| Training | deterministic; two runs produce byte-identical model artifacts |
| Baseline quality | average precision **0.801** on a time-ordered holdout |
| Release identity | source commit + data fingerprint + artifact checksum |
| Tests | 52 offline tests at the M1 checkpoint |

The baseline is a training result, not an operational claim. M2 creates the first serving
measurement.

## Evidence rules

- An image is immutable only when the exact artifact and release identity are bound to its
  digest; a mutable alias is not deployment identity.
- Probe, request, limit, rollout and HPA decisions are written by the author after a falsifying
  scenario and then tested in `kind`.
- p95/p99 is reported only with hardware, payload, concurrency, duration and raw output.
- RED and saturation queries are checked against a hand-written synthetic timeline before a
  dashboard can be evidence.
- A short local test is never described as a monthly SLA.

## Explicitly deferred

The following are deferred:

- M5/M6 concepts: Redis, Kafka and their failure drills;
- MLflow lifecycle and registry state machine;
- automated canary analysis and rollback;
- Terraform, AWS/EKS, cloud IAM and GitHub OIDC;
- a second workload and generic reusable-platform adoption claim;
- full OpenTelemetry/Grafana and a long-horizon SLO/error-budget story.

Their earlier detailed draft remains in Git history; it is not the
current roadmap.

## Scope boundaries

- One small CPU model; no modelling competition.
- Local-first: container plus `kind`, without cloud work in M1–M4.
- Native Kubernetes semantics before rollout automation.
- No feature store, custom orchestrator, service mesh, multi-region, GPU or distributed
  training.
- No production availability claim from a portfolio benchmark.

## Reproduce M1

```bash
make install   # sync the pinned environment
make check     # ruff + tests
make data      # fetch and fingerprint the source dataset once
make train     # deterministic fit; writes local artifact, metrics and release record
```

Raw data, model artifacts and local release records are not committed.

## Documents

- [Development plan](docs/development-plan.md) — M1–M4 order and acceptance rules.
- [Architecture](docs/architecture.md) — planned boundaries and failure model.
- [Reliability protocol](docs/reliability-protocol.md) — evidence required for a measurement.
- [Learning contract](LEARNING.md) — author-owned tasks and AI boundaries.
