# План разработки

Редакция 25.08.2026. Активный scope — только M1–M4.

## Цель и объём

Цель — minimum operational surface: один воспроизводимый workload доводится до immutable
локального сервиса, затем его Kubernetes-поведение и service-side метрики измеряются под
объявленной нагрузкой.

| # | Результат | Источник полного плана | Часы | Статус |
|---:|---|---|---:|---|
| M1 | workload и минимальная идентичность релиза | фаза 1 | 6 | **закрыт** |
| M2 | immutable image и локальный baseline | срез фазы 3 | 8 | не начат |
| M3 | `kind`: probes, resources, rollout, PDB, HPA | фаза 4 | 14 | не начат |
| M4 | RED, in-flight, saturation и p95/p99 | срез фазы 5 | 6 | не начат |

Итого 34 часа, закрыто 6, осталось **28 часов**. Календарная дата не
подменяет evidence: незакрытый milestone остаётся незакрытым.

## M1 — workload и release identity · закрыт

Есть data/model contract, детерминированный training path, fingerprint данных, input/output
signature и локальный release record. Текущий release identity связывает source commit,
dataset fingerprint и checksum артефакта.

Ограничение фиксируется явно: это ещё не lifecycle state machine, registry, image или release
в среду. Порог решения в workload остаётся `UNSET` до авторского анализа precision/recall.

Acceptance evidence:

- две тренировки дают byte-identical artifact;
- incompatible schema ломает contract test;
- release record создан на clean HEAD и содержит `source_dirty=false`;
- все M1-тесты проходят offline.

## M2 — immutable image и локальный baseline · 8 ч

Сначала автор фиксирует контракт сервиса и failure modes, затем пишет falsifying fixtures.

- golden request/response и точная input schema;
- malformed и incompatible request;
- startup при отсутствующем или повреждённом artifact;
- служебный endpoint с exact release metadata;
- graceful shutdown;
- image связывает один release с одним digest;
- cold/warm load baseline с hardware, concurrency, payload и duration.

Готово, когда clean checkout строит exact image, служебный endpoint возвращает его release
identity, а p50/p95/p99 воспроизводятся записанной командой.

## M3 — `kind` operational semantics · 14 ч

Автор сначала объясняет и проверяет каждое решение, а не получает готовый YAML:

- startup отделяет загрузку модели от liveness;
- readiness означает безопасную способность принимать traffic;
- liveness ловит зависание процесса, а не отказ внешней зависимости;
- requests выводятся из измерений, limits проверяются stress-case;
- RollingUpdate сохраняет объявленную ready capacity;
- PDB и graceful termination подтверждаются events;
- HPA имеет определённый denominator и реально меняет replica count под нагрузкой.

Готово, когда каждый probe намеренно становился красным, rollout разобран по timeline, а
scaling experiment хранит load, metric source и replica history.

## M4 — RED и latency evidence · 6 ч

Минимальный срез наблюдаемости:

- request rate, error rate, duration и in-flight;
- CPU/memory saturation, restarts и desired/ready replicas;
- точная deployed release identity без high-cardinality labels;
- p50/p95/p99 со стороны сервиса под тем же declared load profile.

PromQL сначала проверяется на ручном synthetic timeline: error request не исчезает из
denominator, timeout считается ошибкой, saturation не заменяется CPU utilization. Dashboard,
полный OTel tracing и monthly error budget не входят в M4.

Готово, когда raw output, запросы, окно наблюдения, hardware и конфигурация сохранены, а вывод
называется bounded benchmark, не SLA.

## Отложено

До отдельного решения не открываются:

- M5 Redis и M6 Kafka;
- MLflow tracking/registry и полная release state machine;
- canary automation, rollback controller и расширенные drills;
- Terraform/AWS/EKS/OIDC;
- второй workload и reusable-platform adoption claim;
- full OTel/Grafana и долгосрочный SLO/error budget.

Решение о возврате требует закрытых M1–M4 и измеренного пробела. Предыдущая подробная M5/M6 редакция сохранена в
Git-истории, но не является действующим планом.

