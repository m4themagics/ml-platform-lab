# Workloads

Each workload owns what its data means. None of them owns the release path.

| # | Workload | Input → output | State |
|---:|---|---|---|
| 1 | [`fraud_scoring`](fraud_scoring/README.md) | 29 numeric features → P(fraud) | contract, deterministic training and release record |
| 2 | `text_moderation` | short text → label + score | not started, opens at phase 8 |

The second workload exists to test the boundary, not to add a feature. Its schema is deliberately
of a different kind — a string rather than a fixed-width numeric row — so a platform layer that
secretly assumes tabular input fails visibly instead of quietly.

Selection criteria, in order: trains on CPU in minutes, makes schema and quality failure fixtures
easy to inspect, and has an operational story where latency and silent degradation actually cost
something. Model novelty is explicitly not a criterion.
