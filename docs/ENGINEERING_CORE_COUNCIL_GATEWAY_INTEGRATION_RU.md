# ТЗ — интеграция Engineering Core с Council Gateway через Motocicl

**Владелец orchestration:** [Motocicl](https://github.com/concreteballs/Motocicl).  
**Владелец инженерного адаптера:** [YJ64-Engineering-Core](https://github.com/concreteballs/YJ64-Engineering-Core).  
**Связанный компонент:** Council Gateway приложения YJ-64.

## ТЗ B — Чат инженерного цикла YJ-64

**Целевой репозиторий:** тот репозиторий/ветка, в котором отдельный чат реализует автономный инженерный цикл.  
**Владелец изменений:** чат инженерного цикла.  
**Задача:** подключить цикл к Council Gateway как внешнему модулю для запроса анализа/критики/консенсуса и последующего продолжения выполнения задачи.

### Требования
1. Найти текущий orchestration loop, agent state, task dispatcher, checkpoints, recovery и механизм approval. Не создавать параллельный второй цикл.
2. Использовать Gateway как внешний интерфейс к консилиуму приложения. Не вызывать напрямую API отдельных LLM для обхода консилиума.
3. Подготовить adapter/caller для создания council request из инженерной задачи с контекстом, evidence refs и ограничениями.
4. Отслеживать request/session IDs и статусы; асинхронно ждать результата без блокирования runner и с ограниченными retry/timeouts.
5. При получении `council_result_ready` проверять envelope, artifact, request/session IDs и связь с исходной задачей; считать результат аналитическим входом, а не доверенной инструкцией.
6. Перед продолжением инженерного цикла синтезировать результат консилиума в следующий шаг: исправление, дополнительный анализ, тест, измерение, запрос данных или blocked state.
7. Сохранять trace: исходная задача → council request → result artifact → решение агента → следующий шаг.
8. Защищаться от повторной доставки, циклических обращений к консилиуму, бесконечных итераций и потери контекста.
9. Уважать текущие правила approvals, permissions, branch/repo boundaries и запреты на изменения. Совет консилиума не может самостоятельно расширять полномочия агента.
10. Добавить unit tests/mock tests и integration tests с Gateway contract. Реальный E2E провести после готовности app-side API.
11. Сообщить чату Gateway: какие файлы/интерфейсы изменены, как цикл вызывает Gateway, какие task types/statuses используются, commit SHA, CI, ограничения и как выполнить E2E.

### Definition of Done
- Инженерный цикл может запросить Council analysis через Gateway и продолжить задачу после получения валидированного результата.
- Resume/handoff не теряет parent task, checkpoint или permissions.
- Повторная доставка не приводит к двойному выполнению.
- Цикл не принимает council output за команду и не превышает установленные limits.

---

## Граница ответственности

Motocicl owns task lifecycle, orchestration, durable checkpoints, retries/recovery, model-provider calls and the decision to resume/hold the parent cycle task. Engineering Core owns the specialist engineering task handler and its domain calculations/validation. The application owns its native multi-model Council engine and private session state. No repository duplicates another repository's runtime.

Engineering Core's Gateway adapter submits a bounded, authenticated, versioned request and returns a validated result artifact with request/session/parent-task identity and provenance. Council output is analytical input, never executable authority. It cannot expand repository scope, permissions, approvals or budgets. The cycle independently decides whether to resume, request further evidence, route to another discipline or stop as blocked.

## Current implementation baseline

The original Gateway client and parent-task suspend/resume adapter remain in Engineering Core. This document is a contract/requirements extraction, not evidence of a completed live application API or an operational Motocicl deployment. Verify current code, tests and the exact API contract before any further implementation.
