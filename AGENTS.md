# Working context for agents

Read this before touching anything. This repository is paused. Do not advance a phase unless the author explicitly
reopens it. For preserved context, read
[README.md](README.md), then
[docs/development-plan.md](docs/development-plan.md) and [LEARNING.md](LEARNING.md).

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

Paused at phase 0. Documentation, a decision config and scaffold tests exist. There is no deployed
service, local cluster, cloud resource, MLflow run or benchmark result yet. Unset thresholds in
`configs/platform.toml` are intentional and must be decided before the first measured run.
