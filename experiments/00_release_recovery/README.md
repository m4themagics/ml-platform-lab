# Experiment 00 — can the release path recover before its bounded objective is exhausted?

Status: **draft preregistration; blocked until phases 1–5 exist.** Threshold values remain
`UNSET` in `configs/platform.toml` and must be fixed before the first candidate drill.

## Question

Under a fixed request load, can the same automated path:

1. promote a healthy candidate;
2. stop a deterministic latency regression;
3. restore the previous exact image/model release;
4. keep availability and latency within the preregistered bounded objective?

## Why this is experiment 00

The repository's central claim is recovery, not component installation. If this smallest
failure cannot be detected and reversed reliably, AWS, Kafka and a second workload add surface
area without strengthening the result.

## Fixed before the run

- healthy and delayed candidate digests;
- exact model versions and identical request schema;
- load distribution, concurrency/arrival rate, warm-up and duration;
- PromQL for availability and p95/p99;
- canary share and analysis window;
- violation, detection and recovery timestamps;
- rollback threshold and missing-telemetry behaviour;
- number of repetitions and abort conditions.

## Correctness gates

- The delay fixture is the only difference between candidates.
- The load generator runs outside the candidate pods.
- Both releases pass offline model/schema checks.
- Client results and Prometheus counters agree within an explained tolerance.
- The previous release is addressed by exact digest/version, not `latest` or alias.
- Rollback success requires a stable healthy window, not a controller status alone.

## Output

One evidence bundle per repetition and a report containing promotion outcome, request counts,
availability, p50/p95/p99, MTTD and MTTR. A negative result is retained and becomes the next
design input.
