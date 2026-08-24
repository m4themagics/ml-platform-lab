# Working context for agents

Read this before touching anything. This repository is active again as of 2026-08-24.
The scope is deliberately narrow — a minimum operational surface (probes, rollout, resource sizing, p95/p99),
not the full twelve-week Must. Do not start work outside that surface, and do not restart the
deferred phases (2, 6–9) without the author saying so. For context, read
[README.md](README.md), then
[docs/development-plan.md](docs/development-plan.md) and [LEARNING.md](LEARNING.md).

Resumed work does not relax the rule below. It makes it load-bearing: the surface is made almost
entirely of the author's central learning tasks.

## The rule that overrides default implementation behaviour

This repository exists to build operational judgment, not to accumulate generated YAML.
**Do not implement the central learning tasks for the author.** Those include:

- the model/release contract and its state transitions;
- Kubernetes probes, resource sizing, autoscaling and rollout manifests;
- PromQL SLI/SLO queries and alert conditions;
- Terraform IAM, networking, EKS and remote-state design;
- automated promotion/rollback logic;
- Kafka partitioning, idempotency, retry and replay semantics if that extension opens.

For these tasks, ask for the author's hypothesis or first draft, give one hint at a time,
review it, and help construct falsifying tests. A finished implementation is written only
after the author has attempted it and explicitly asks for the solution.

Mechanical work is allowed: repository plumbing, formatting, CI wiring, fixtures requested by
the author, documentation edits, and tests that encode a contract the author has already
defined.

If unsure whether something is central, treat it as central and ask before implementing it.

## Evidence rules

- A component does not exist because it appears in a diagram. Status must match executable
  state.
- Every release result links commit, data fingerprint, MLflow run and model version, image
  digest, configuration snapshot and cluster version.
- A mutable model alias is never the final deployment identity.
- A reliability result records the load profile, time window, raw outputs, Prometheus queries,
  rollout events and detection/recovery timestamps.
- A short drill is not described as a monthly availability SLA.
- Cloud work has a reviewed destroy path and cost guardrails before `terraform apply`.
- Failure results are retained. A rollback that fails is evidence, not a run to erase.

## Conventions

- Docs and commit bodies in Russian; code, docstrings and commit subjects in English.
- Commit subjects: `feat:`, `fix:`, `docs:`, `test:`, `chore:`; lowercase, no trailing period.
- Python 3.12 and `uv`; `make check` must pass before a push.
- Terraform state, credentials, kubeconfigs, raw run payloads and model artifacts are never
  committed.
- Keep local and cloud interfaces aligned, but do not pretend they have identical failure
  modes.
- Add a dependency or platform component only with the failure mode or evidence it enables.

## Current state

Active, entering M1 of the minimum operational surface. Phase 0 is closed as scaffold:
documentation, a decision config and scaffold tests exist. There is no deployed service, local
cluster, cloud resource, MLflow run or benchmark result yet, and `configs/platform.toml` still
declares `status = "scaffold"` because executable state has not moved. Unset thresholds there are
intentional and must be decided by the author before the first measured run.

The current target is the minimum operational surface only — M1 workload slice, M2 immutable
image and local baseline, M3 `kind` probes/resources/rollout, M4 RED metrics for a served
p95/p99. MLflow, canary automation, Terraform, the second workload and the final reproduction
report are explicitly deferred. Widening that scope is the author's decision, not an agent's.
