# Learning contract

Этот репозиторий существует ради навыка проектировать и эксплуатировать ML-платформу, а не
ради количества сгенерированных манифестов.

## Когда результат считается моим

Компонент можно отметить как освоенный, только если я могу без подсказки:

1. объяснить его контракт, границы ответственности и владельца состояния;
2. провести один запрос или релиз по всем переходам состояния;
3. назвать failure modes и сигнал, по которому каждый из них обнаруживается;
4. сначала создать отрицательный тест или drill, затем исправить поведение;
5. объяснить least-privilege и cost trade-offs;
6. воспроизвести результат из clean checkout записанной командой;
7. провести teach-back без чтения YAML, Terraform или кода.

## Как использовать AI

Для model contract, Kubernetes, observability, Terraform, release automation и Kafka по
умолчанию действует такой режим:

- сначала я пишу схему, гипотезу, PromQL/Terraform/YAML draft или ожидаемый state transition;
- AI задаёт вопросы, даёт одну подсказку и ревьюит мою попытку;
- AI может сделать механический plumbing и тестовые fixtures;
- AI не проектирует за меня IAM, probes, SLO, rollback state machine или delivery semantics;
- готовую реализацию запрашиваю только после своей попытки и отдельным явным решением;
- вывод из drill формулирую я после ручного разбора timeline и telemetry.

Полезные формулировки:

- «не пиши manifest; спроси, что именно должна доказывать readiness probe»;
- «проверь мой PromQL на потерю failed requests»;
- «дай один failure mode для этого IAM policy»;
- «помоги написать падающий contract test, не исправляя код»;
- «сделай review плана rollback и попроси меня выбрать trade-off».

## Ownership tracker

Уровни: `0` — не начинала, `1` — объясняю, `2` — меняю и тестирую,
`3` — защищаю эксплуатационный вывод.

| Область | Фаза | Уровень | Моё доказательство |
|---|---:|---:|---|
| data/model/release identity contract | 1 | 0 | |
| MLflow run, registry version, aliases and lineage | 2 | 0 | |
| immutable OCI image and dependency closure | 3 | 0 | |
| FastAPI serving and schema compatibility | 3 | 0 | |
| startup/readiness/liveness semantics | 4 | 0 | |
| requests, limits, saturation and HPA | 4 | 0 | |
| RED metrics and OpenTelemetry traces | 5 | 0 | |
| SLI, bounded SLO and error budget | 5 | 0 | |
| rollout analysis and rollback state machine | 6 | 0 | |
| failure-drill design and timeline reconstruction | 6 | 0 | |
| Terraform modules, state and drift | 7 | 0 | |
| AWS IAM and GitHub OIDC | 7 | 0 | |
| reusable path for a second workload | 8 | 0 | |
| clean-checkout cloud reproduction | 9 | 0 | |
| Kafka delivery, idempotency and lag | Should | 0 | |

Таблицу заполняю только я.

## Шаблон рабочей записи

```text
Дата / commit:
Компонент или drill:
Контракт и владелец состояния:
Моя гипотеза:
Failure mode и ожидаемый сигнал:
Мой draft / diagram / query:
Что реализовала сама:
Где использовала подсказку:
Команда и конфигурация:
Commit / data fingerprint / MLflow run / model version / image digest:
Нагрузка и окно наблюдения:
Timeline обнаружения и восстановления:
Результат и сырые evidence paths:
Cost / security trade-off:
Что теперь могу объяснить:
Следующий маленький шаг:
```
