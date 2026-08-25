# План разработки

Редакция 2026-08-21, ревизии 24.08.2026 и 25.08.2026. Пауза снята частично. Двенадцатинедельный календарь Must ниже читается как
порядок работ, а не как расписание. Активный объём — раздел «Возврат: minimum operational
surface»; всё остальное ниже сохраняется как справочный полный путь.

Ревизия 25.08.2026 добавляет два шага после поверхности —
M5 и M6. Обоснование и отбор — раздел «Расширение: M5 и M6».

## Зачем этот репозиторий

Коммерческий опыт уже доказывает умение построить модель и завернуть её в API. Здесь нужно
закрыть другой сигнал: спроектировать повторяемый путь для нескольких ML-нагрузок, связать
модель с инфраструктурой и уметь объяснить поведение системы при отказе.

Центральный результат — не «MLflow поднялся» и не «pod зелёный». Это таблица контролируемых
релизов и отказов, где для каждого случая известны:

- commit, data fingerprint, MLflow run и точная версия модели;
- digest образа и применённая конфигурация;
- нагрузка и окно наблюдения;
- SLI до, во время и после релиза;
- timeline обнаружения, остановки rollout и восстановления;
- команда воспроизведения и raw evidence.

## Что считается reusable platform tooling

Один workload ничего не доказывает про платформу: общие функции могут быть просто
application code. Поэтому Must заканчивается только после второго workload, который проходит
тот же контракт и delivery path без копии pipeline или отдельного набора Kubernetes YAML.

Переиспользуемый слой владеет только тем, что действительно общее:

- идентичность релиза и model contract;
- validation gates;
- упаковка и immutable deployment reference;
- observability contract;
- rollout/rollback interface;
- evidence bundle.

Feature engineering, model metric и входная schema остаются у workload. Если общий слой
начинает знать их бизнес-смысл, граница проведена неверно.

## Объём и порядок

| # | Результат | Часы | Календарный gate |
|---:|---|---:|---:|
| 0 | scope, architecture, protocol, cost gates | 4 | неделя 1 |
| 1 | первый workload и data/model/release contract | 10 | неделя 2 |
| 2 | MLflow tracking, registry, lineage и candidate version | 12 | неделя 3 |
| 3 | immutable image, API contract, локальный benchmark | 10 | неделя 4 |
| 4 | `kind`: probes, resources, disruption и HPA | 14 | неделя 5 |
| 5 | OTel, Prometheus/Grafana, SLI и bounded SLO | 14 | неделя 7 |
| 6 | canary analysis, promotion, automated rollback, drills | 16 | неделя 8 |
| 7 | Terraform + AWS/EKS + GitHub OIDC + destroy path | 20 | неделя 10 |
| 8 | второй workload через тот же golden path | 8 | неделя 11 |
| 9 | clean-checkout reproduction и итоговый failure report | 8 | неделя 12 |

Must занимает 116 часов; четыре часа — резерв. Даты не двигаются автоматически: при
перерасходе режется компонент, который не доказывает центральный вопрос.

Первый внешний результат должен появиться к концу четвёртой недели: один model version,
immutable image и честный локальный latency baseline. Он ещё не доказывает платформу, но уже
даёт проверяемый end-to-end slice.

---

## Возврат: minimum operational surface

Активный объём с 24.08.2026. Не весь Must ниже, а минимальная эксплуатационная поверхность:
сервис в `kind`, у которого probes действительно что-то различают, rollout не роняет ready
capacity, requests и limits выведены из измерений, а p95/p99 назван вместе с нагрузкой и окном
наблюдения.

Почему режется именно так. Центральный вопрос репозитория — управляемый релиз и восстановление.
Ни registry, ни cloud не приближают к нему, пока нет работающего сервиса, на котором измерена
деградация. Поверхность — кратчайший путь до первого проверяемого эксплуатационного результата;
после него становится осмысленным эксперимент 00.

| # | Шаг | Источник | Часы | Что урезано относительно фазы |
|---:|---|---|---:|---|
| M1 | workload и минимальная идентичность релиза | фаза 1 | 6 | остаются data contract, детерминированное обучение, fingerprint и input/output signature; полная release state machine откладывается вместе с фазой 2 — идентичность на этом шаге это commit + fingerprint + image digest |
| M2 | immutable image и локальный baseline | фаза 3 | 8 | остаются golden request/response, malformed request, graceful shutdown и локальный load test; служебный endpoint отдаёт release metadata без registry |
| M3 | `kind`: probes, resources, rollout, HPA | фаза 4 | 14 | ничего; это ядро поверхности |
| M4 | RED-метрики и p95/p99 со стороны сервиса | срез фазы 5 | 6 | остаются request rate, error rate, duration, in-flight и saturation с проверенным вручную PromQL; OTel traces, Grafana и error budget откладываются |

Итого 34 часа, из них M1 закрыт — остаётся 28. Календарные гейты Must пересчитываются
только после того, как поверхность закрыта, — не заранее.

### Отложено до закрытия поверхности

- фаза 2 — MLflow tracking, registry и lineage;
- фаза 6 — canary analysis, автоматический rollback и drills;
- фаза 7 — Terraform, AWS/EKS и GitHub OIDC;
- фаза 8 — второй workload;
- фаза 9 — clean-checkout reproduction и итоговый failure report.

Профильные шаги M5 и M6 («Профильный контур») тоже ждут закрытия поверхности, но идут перед
фазами 2, 6 и 7.

Отложенное не удаляется и не переписывается: пока поверхность не закрыта, оно просто ждёт.

### Решения до первого измеренного прогона

Из `configs/platform.toml` к поверхности относятся `project.primary_workload`,
`release_gates.quality_threshold`, `slo.p95_latency_ms`, `slo.p99_latency_ms`,
`slo.observation_window` и `slo.load_profile`. Они меняются до прогона, не после. Остальные
`UNSET` принадлежат отложенным фазам и остаются нетронутыми — их видимая незаполненность и есть
честный статус.

### Готово, когда

- каждый probe хотя бы раз намеренно красный, и различие startup/readiness/liveness объяснено на
  событии, а не на YAML;
- rollout разобран по events: ready capacity не опускалась ниже объявленного минимума;
- requests выведены из измерения, limits проверены отдельным stress case;
- p95/p99 и error rate считаются запросом к метрикам сервиса и сходятся с клиентским
  результатом в объяснённом допуске;
- цифры названы bounded benchmark objective с hardware, concurrency, payload и длительностью —
  не SLA и не availability за месяц;
- всё воспроизводится из clean checkout записанной командой.

Поверхность не закрывается зелёным подом. Она закрывается разобранным таймлайном.

---

## Расширение: M5 и M6

Добавлено 25.08.2026. Три вещи, которые проект ещё не покрывает: Redis в горячем пути,
интеграция через шину или очередь, безопасный
вывод версии модели с откатом. Третье уже принадлежит Must (фазы 2 и 6). Первые два получают
шаги M5 и M6 — после закрытия поверхности, не вместо неё.

Правило отбора не меняется и здесь: инструмент входит только вместе с контрактом отказа и
drill. Producer и consumer без failure contract, как и Redis без сценария его недоступности,
доказательством не являются.

Что сознательно не добавляется:

- **Airflow** — причина из «Чего в Must нет» остаётся верной: один линейный training job не
  требует orchestrator, и DAG ради галочки видно за минуту. Пробел закрывается в
  `marketplace-ranking-lab`, где backfill фичей и temporal evaluation действительно требуют
  расписания и зависимостей между задачами.

| # | Шаг | Часы | Что доказывает |
|---:|---|---:|---|
| M5 | Redis в горячем пути инференса | 7 | сервис переживает отказ внешней зависимости; цена и выигрыш кэша измерены |
| M6 | Kafka audit path | 16 | асинхронная интеграция с идемпотентностью и recovery без двойного счёта |

M6 — это бывший Should, поднятый **выше фазы 7** (Terraform/AWS, 20 ч). Порядок после
поверхности: M5, M6, затем отложенные фазы 2 и 6.

### M5 — Redis в горячем пути (7 ч)

Это не feature store: запрет из «Чего в Must нет» остаётся в силе, online/offline consistency
не доказывается и не заявляется. Это read-through кэш ответов инференса, оправданный
центральным вопросом — у сервиса появляется внешняя зависимость, отказ которой обязан
деградировать, а не ронять.

| Задача | Часы | Результат |
|---|---:|---|
| Read-through кэш; ключ включает model version и release id | 1,5 | новая версия модели не отдаёт ответы предыдущей; TTL и политика ключа записаны в `configs/platform.toml` |
| Контракт отказа: таймаут обращения к Redis внутри latency-бюджета, деградация на прямой вызов модели | 1,5 | недоступный Redis повышает latency и не повышает error rate; `cache_hit`, `cache_miss`, `cache_error` в метриках |
| Redis в `kind`: resources, probes, поведение при рестарте пода | 1,5 | рестарт зависимости разобран по events, а не по «сервис вроде живой» |
| Drill «Redis unavailable under load» по протоколу надёжности | 2 | строка в Results: availability, p95/p99 с кэшем и без, detection time, recovery time |
| ADR: кэш вместо feature store, read-through вместо write-through, версия модели в ключе | 0,5 | решение с отвергнутыми альтернативами и их ценой |

Готово, когда p95/p99 названы двумя числами — с прогретым кэшем и при недоступном Redis — на
одном и том же load profile, и разница объяснена, а не показана.

### M6 — Kafka audit path (16 ч)

Полный контракт — в разделе «Should: Kafka audit path». Разбивка по задачам:

| Задача | Часы | Результат |
|---|---:|---|
| Контракт события: schema, key/partitioning, idempotency key, retention, эволюция схемы | 2 | событие описано до первого producer, а не после |
| Producer в inference: запись не блокирует ответ; решение о поведении при недоступном брокере | 3 | request latency не зависит от брокера; выбор между буфером и drop зафиксирован в ADR с ценой |
| Consumer: at-least-once, идемпотентная запись, retries/backoff, poison message → DLQ | 3 | повтор доставки не меняет результат; отравленное сообщение не останавливает поток |
| Drills: duplicate, reorder, consumer restart, broker down | 4 | строки в Results с recovery without double-counting |
| Consumer lag under load и alert на нём | 2 | лаг измерен под объявленной нагрузкой, порог назван до прогона |
| Runbook | 2 | что делает дежурный при растущем лаге и при DLQ, проверено на drill |

Готово, когда duplicate- и restart-drill не меняют итоговый счёт событий, а лаг возвращается
к норме за названное время.

---

## 0 — scope и gates (4 ч)

До кода фиксируются:

- первый workload и маленький golden dataset;
- граница workload/platform;
- формат data fingerprint, model version и release manifest;
- load profile и определения SLI;
- thresholds эксперимента 00;
- локальный и cloud cost envelope;
- владельцы состояния и список секретов;
- teardown и recovery expectations.

`UNSET` в `configs/platform.toml` меняется до первого измеренного прогона, не после него.

**Готово, когда** один релиз можно провести на sequence diagram с точными идентификаторами и
назвать, где он обязан остановиться при несовместимой schema.

## 1 — workload и три контракта (10 ч)

Модель намеренно мала и обучается на CPU за минуты. Нужны три разных контракта:

1. **Data contract:** schema, target, split, fingerprint и допустимые missing values.
2. **Model contract:** input/output signature, metric, golden examples и compatibility rule.
3. **Release contract:** commit, run, registered model version, image digest, config и status
   transitions.

Центральное учебное упражнение — state machine релиза. Минимальные состояния:
`trained → evaluated → registered → packaged → candidate → promoted` с явными rejected и
rolled-back ветками. Переход не должен выводиться из имени файла или mutable alias.

**Готово, когда** incompatible fixture сначала ломает contract test, а совместимая модель
воспроизводится из data fingerprint и seed.

## 2 — MLflow lifecycle (12 ч)

Локально: database-backed tracking/registry store и отдельное artifact storage. Run хранит
params, metrics, signature, dataset fingerprint и source commit. Registry version получает
validation tags; alias используется как указатель candidate/champion, но delivery pipeline
разрешает его в точную версию до сборки.

Не используется deprecated stage-based workflow. Не регистрируется модель, которая не
прошла quality и schema gates.

**Готово, когда** из release manifest можно двусторонне перейти к run, model version и
artifact checksum, а удалённый или подменённый artifact обнаруживается тестом.

## 3 — immutable serving slice (10 ч)

Inference image содержит точную модель или получает её на build step; runtime не зависит от
того, куда завтра переведут alias. API валидирует schema, возвращает model/release metadata в
служебном endpoint и не логирует чувствительные признаки.

Сначала:

- golden request/response;
- malformed и incompatible requests;
- startup с отсутствующим/повреждённым artifact;
- graceful shutdown;
- cold и warm local load test.

**Готово, когда** один immutable digest связан с одной model version и есть baseline
p50/p95/p99 с hardware, concurrency, payload и duration.

## 4 — Kubernetes до автоматики (14 ч)

Сначала native Deployment в `kind`, чтобы понимать механику, которую позже скрывает rollout
controller:

- startup probe отделяет загрузку модели от liveness;
- readiness отвечает только на способность безопасно принимать traffic;
- liveness ловит зависание процесса, а не внешнюю зависимость;
- requests следуют из измерений, limits проверяются отдельным stress case;
- RollingUpdate не снижает ready capacity ниже declared minimum;
- PodDisruptionBudget и graceful termination проверяются событием, а не наличием YAML;
- HPA получает метрику и реально меняет replicas под нагрузкой.

CPU HPA не открывается до requests: без denominator utilization не определена.

**Готово, когда** каждый probe хотя бы раз намеренно красный, rollout timeline разобран по
events, а scaling experiment показывает load, metric source и replica history.

## 5 — observability и bounded SLO (14 ч)

OpenTelemetry переносит traces/metrics к collector; Prometheus хранит операционные SLI,
Grafana только визуализирует уже проверенные запросы. Минимум:

- request rate, error rate, duration и in-flight requests;
- CPU/memory saturation, restarts, desired/ready replicas;
- deployed release, model version и prediction distribution без high-cardinality labels;
- один trace через входной запрос и внутренний model call;
- pipeline freshness для training/release path.

Сначала запросы проверяются на синтетическом timeline руками. Dashboard не является тестом
корректности PromQL.

**Готово, когда** error request не исчезает из denominator, timeout считается unavailable,
а наблюдаемый window называется benchmark objective, не monthly SLA.

## 6 — безопасный delivery и failure drills (16 ч)

После native rollout добавляется автоматизированный candidate flow. Реализация может
использовать Argo Rollouts или небольшой orchestration layer, но выбор фиксируется ADR по
минимальному failure surface.

Обязательные ветки:

- candidate не проходит offline quality gate;
- schema incompatibility не доходит до traffic;
- crash loop не заменяет healthy replicas;
- latency/error regression останавливает promotion и возвращает предыдущий digest;
- registry недоступен во время rollout;
- telemetry частично недоступна — безопасное поведение явно выбрано: fail closed или hold.

Drill повторяется заранее заданное число раз. Отчёт содержит MTTD и MTTR с определениями
начала/конца, а не только `kubectl rollout status`.

## 7 — AWS/Terraform (20 ч)

Cloud открывается только после локального end-to-end и working destroy path.

Terraform владеет:

- bootstrap state storage отдельно от основного stack;
- версионированным и зашифрованным S3 state с locking;
- network и EKS dependencies;
- registry/artifact resources, IAM roles и policies;
- GitHub OIDC trust вместо long-lived access keys;
- owner/TTL/cost tags и outputs для smoke/destroy.

Dev/prod имеют отдельные state/config boundaries. Один учебный AWS account или один cluster
не называется полноценной account isolation; это ограничение явно остаётся в отчёте.

Cloud experiment: clean account prerequisites → plan review → apply → deploy exact release →
smoke/load slice → capture evidence → destroy → independent check на оставшиеся billable
resources.

**Готово, когда** нет console-only шага, policy объясняется action/resource/condition, state
не локален, apply воспроизводим, destroy проверен, а фактическая стоимость записана.

## 8 — второй workload (8 ч)

Выбирается модель с другой input/output schema. Нельзя копировать pipeline и менять имена.
Допустимы workload-owned adapter, metric и golden fixtures; platform contract, gates,
observability и deploy template остаются общими.

**Стоп-условие:** если для второго workload приходится добавить domain-specific ветку в
platform layer, сначала пересматривается граница абстракции.

**Готово, когда** оба релиза проходят одной командой с разными config, и отчёт показывает,
какой код общий, какой workload-owned и сколько ручных шагов осталось.

## 9 — reproduction и упаковка (8 ч)

- clean-checkout local run;
- отдельный clean cloud run;
- полный healthy + failed release drill;
- проверка runbooks другим человеком или dry run без скрытого контекста;
- итоговая architecture diagram: `planned` заменяется только на реально deployed;
- README results заполняются ссылками на evidence bundles;
- CV bullets пишутся только из измеренных фактов.

---

## Should: Kafka audit path (16 ч, шаг M6)

С 25.08.2026 это шаг **M6** профильного контура, а не хвост после Must: он идёт сразу за M5 и
перед фазой 7. Разбивка по задачам — в разделе «Профильный контур».

Kafka открывается, когда есть реальная причина отвязать request latency от записи inference
events. Контракт включает key/partitioning, at-least-once semantics, idempotency key,
retries/backoff, poison message path, retention и schema evolution.

Доказательство — не throughput producer. Нужны duplicate/reorder/restart drills, consumer lag
under load, recovery without double-counting и alert/runbook. В AWS реализация выбирается по
цене и operational surface; дорогой managed cluster не является обязательным доказательством.

## Чего в Must нет

- feature store и online/offline consistency — нет workload, который это оправдывает;
- Airflow/Kubeflow — один линейный training job не требует нового orchestrator;
- service mesh, multi-region и multi-cluster — не нужны центральному вопросу;
- custom Kubernetes operator — сначала используются стандартные controllers;
- GPU, multi-node training и Triton — модель специально CPU-small;
- «99.99% availability» из десятиминутного теста;
- security theatre из списка сканеров без threat model и blocking gate;
- второй dashboard, пока первый PromQL не проверен руками.

## Активный объём

Активный объём — minimum operational surface (probes, rollout, resource sizing, p95/p99), а не
весь двенадцатинедельный Must ниже. M5 и M6 открываются только после того, как поверхность
закрыта.

Если объём приходится резать, M1–M4
не разбиваются на «почти сделанные» куски. Незакрытый шаг откатывается к предыдущему честному
статусу.
