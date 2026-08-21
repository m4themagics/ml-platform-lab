# Reliability protocol

Правила, которым должен удовлетворять результат, чтобы попасть в README или `reports/`.
Пустые поля заполняются до первого measured run. Если порог меняется после просмотра данных,
старый run остаётся, а изменение получает новую revision и объяснение.

## Preregistration

```text
Scenario / failure:
Expected mechanism:
Release A (healthy) identity:
Release B (candidate) identity:
Cluster and dependency versions:
Load generator and location:
Request payload distribution:
Warm-up / duration / concurrency or arrival rate:
SLI queries:
Candidate window:
Promotion / rollback thresholds:
Drill repetitions:
Start event:
Detection event:
Recovery event:
Expected safe behaviour:
Stop / abort conditions:
Raw evidence paths:
```

## SLI definitions

Точные PromQL queries становятся частью preregistration. Минимальные определения:

- **Availability:** успешные ответы на валидные запросы / все валидные запросы. Timeout и
  reset входят в denominator как unavailable. Клиентские schema errors считаются отдельно и
  не могут улучшать availability.
- **Latency:** p50/p95/p99 с указанием, входят ли timed-out запросы. Основная таблица всегда
  стоит рядом с availability, чтобы исключённые failures не улучшали latency молча.
- **Saturation:** CPU и memory относительно requests/limits, throttling, in-flight requests,
  queue depth и ready/desired replicas.
- **Release correctness:** доля traffic на exact candidate digest, число ready replicas и
  факт прохождения каждого gate.
- **Detection time:** от заранее определённого injection/start event до первого machine
  action, который останавливает promotion или инициирует rollback.
- **Recovery time:** от того же start event до устойчивого окна healthy SLI на предыдущем или
  исправленном exact digest.

Короткое окно называется **bounded load-test objective**, не SLO history и не SLA.

## Required release drills

| Drill | Injection | Safe outcome | Главное доказательство |
|---|---|---|---|
| Offline quality rejection | candidate хуже preregistered gate | package/deploy не запускается | gate state transition |
| Schema incompatibility | required field/type changed | candidate rejected before traffic | contract test + no rollout |
| Corrupt/missing model | checksum or artifact unavailable | build/start fails closed | checksum/startup event |
| Crash loop | process exits after start | healthy release retains capacity | ReplicaSet/Pod events |
| Readiness failure | model loaded but cannot safely serve | pod receives no service traffic | probe + EndpointSlice |
| Latency regression | deterministic delay in candidate | promotion stops, previous digest restored | SLI window + revision |
| Registry outage | registry blocked during rollout | running pinned release survives; new release holds | request results + dependency errors |
| Telemetry degradation | collector/export path blocked | declared fail-safe policy and telemetry-loss alert | collector/app metrics |
| Resource pressure | CPU/memory load | scaling or bounded degradation matches hypothesis | utilization + replicas + latency |

Failure fixtures live in `tests/fixtures/` and carry no hidden toggles that bypass the normal
release path.

## Repetition and uncertainty

- Number of repetitions is fixed before the first drill.
- Raw per-request outcomes and per-drill timestamps are retained.
- Report median and tail/range for MTTD/MTTR; add an interval when repetitions justify one.
- A failed rollback is not discarded as an outlier without a preregistered exclusion rule.
- Warm-up, first-run image pulls and cache state are controlled or reported as separate
  conditions.
- Client and server clocks are synchronized or their offset is measured.

## Evidence bundle

Every run stores:

```text
manifest.toml                 immutable identities and config digests
environment.txt               tool, cluster and dependency versions
load-profile.toml             request population and schedule
client-results.*              per-request status and latency
prometheus-queries/           exact queries and exported series
kubernetes-events.*           rollout, pod, probe and scaling events
traces/                       selected trace IDs and exported trace data
timeline.md                   injection, detection, rollback, recovery
cost.md                       cloud resources, duration and observed cost when applicable
conclusion.md                 author interpretation and limitations
```

Large raw payloads remain untracked; the report contains checksums and a durable location.

## Publication gate

A row enters the README only when:

- all immutable identifiers are present;
- the load profile and observation window are explicit;
- SLI queries have a hand-checked synthetic case;
- rollout events and raw client outcomes agree;
- repetitions and exclusions follow preregistration;
- the author reconstructs the timeline and explains the recovery mechanism;
- a clean-checkout reproduction has passed for the relevant environment;
- limitations distinguish local, ephemeral cloud and real production operation.
