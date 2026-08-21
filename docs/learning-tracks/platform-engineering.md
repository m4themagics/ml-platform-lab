# Learning track: ML platform engineering

Это порядок навыков, а не список видео. Каждый модуль заканчивается маленьким failure test и
teach-back. Следующий модуль не открывается, пока предыдущий нельзя объяснить без манифеста.

## 0. Один релиз на бумаге

- Нарисовать путь commit → run → model version → image digest → rollout revision.
- Назвать владельца каждого состояния и mutable pointers.
- Провести healthy и schema-incompatible release вручную по state machine.

**Проверка:** можно ли однозначно ответить, какая модель обслужила конкретный запрос?

## 1. Container как immutable boundary

- layers, build context, multi-stage build и dependency closure;
- tag против digest;
- process signals, PID 1, graceful shutdown;
- non-root runtime, filesystem и secret boundaries;
- cold start и model loading.

**Failure test:** повреждённый artifact и SIGTERM во время запроса.

## 2. Kubernetes request path

- Pod, ReplicaSet, Deployment, Service, EndpointSlice;
- startup/readiness/liveness и их разные владельцы;
- requests, limits, QoS и throttling;
- RollingUpdate, termination, PDB;
- HPA control loop и metric source.

**Failure test:** pod жив, но не ready; затем rollout с crash-loop candidate.

## 3. MLflow lifecycle

- run, artifact, model signature, registry version;
- tags/aliases против exact version;
- backend store против artifact store;
- promotion и lineage;
- model/data/schema validation.

**Failure test:** alias переведён после build — deployed digest не должен измениться.

## 4. Observability

- logs, metrics, traces и correlation;
- RED/USE, label cardinality и exemplars;
- OTel API/SDK/instrumentation/collector boundaries;
- Prometheus counter/histogram semantics;
- SLI, bounded SLO, error budget, alert и runbook.

**Failure test:** timeout и 500 не исчезают из availability denominator.

## 5. Delivery control loop

- offline gate, candidate, promotion и rollback state transitions;
- native rollout before controller abstraction;
- canary window, delayed signals и missing telemetry;
- fail-open/fail-closed/hold choices;
- idempotent retry of CI/deploy steps.

**Failure test:** latency regression и telemetry outage имеют разные safe actions.

## 6. Terraform and AWS

- dependency graph, plan/apply, state and drift;
- modules and environment/state boundaries;
- S3 state encryption/versioning/locking;
- IAM action/resource/condition and trust policy;
- GitHub OIDC and short-lived credentials;
- VPC/EKS/ECR/S3 dependencies;
- cost inventory, TTL and destroy verification.

**Failure test:** concurrent state writer и denied IAM action без console workaround.

## 7. Reusable golden path

- platform-owned vs workload-owned config;
- schema adapter without domain leakage;
- template/version compatibility;
- onboarding lead time and manual-step accounting;
- second workload as falsification of the abstraction.

**Failure test:** workload с другой schema не требует fork pipeline.

## 8. Kafka extension — only after Must

- partition key and ordering scope;
- producer acknowledgment and retry duplication;
- consumer groups, offsets and rebalance;
- at-least-once processing and idempotency key;
- schema evolution, poison messages, replay and lag.

**Failure test:** duplicate + restart + replay do not double-count audit events.
