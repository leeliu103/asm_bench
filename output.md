# Output Format

This file defines the required benchmark output layout.

Each benchmark run writes all outputs under the configured run directory:

```text
runs/<run_id>/
```

The master must write:

```text
runs/<run_id>/report.md
runs/<run_id>/<task_name>/attempt_N.s
```

Do not write plots, generated analysis scripts, CSV files, JSON files, or harness logs unless explicitly requested.

## Attempt Snapshots

Before each official evaluation, copy the submitted candidate file:

```text
tasks/<task_name>/candidate.s
```

to an immutable attempt snapshot:

```text
runs/<run_id>/<task_name>/attempt_N.s
```

Then evaluate the snapshot, not the mutable task candidate:

```bash
./harness.py --task <task_name> --candidate runs/<run_id>/<task_name>/attempt_N.s
```

`N` starts at `1` for each task.

Only create snapshots for official attempts that actually happened. If a task passes on attempt 1, do not create `attempt_2.s` or later files for that task.

## report.md

`report.md` is the human-readable benchmark result.

It should be concise and should not include full harness logs.

Required structure and example:

```md
# Benchmark Report

run_id: 20260511_153012_123456
agent: codex
k: 3
total_tasks: 3

## Summary

pass@1_success_rate: 1/3 = 0.333
pass@k_success_rate: 2/3 = 0.667
passed_tasks: 2
failed_tasks: 1

## Task Results

| task | result | pass@1 | pass@k | attempts |
|---|---|---|---|---:|
| simple_add | PASS | true | true | 1 |
| matmul | PASS | false | true | 2 |
| conv2d | FAIL | false | false | 3 |

## Attempts

### simple_add

| attempt | result | result_summary | candidate |
|---:|---|---|---|
| 1 | PASS | official harness exited 0; [result] PASS | `runs/20260511_153012_123456/simple_add/attempt_1.s` |

### matmul

| attempt | result | result_summary | candidate |
|---:|---|---|---|
| 1 | FAIL | official harness exited nonzero; n=1024 output mismatch: idx=17 | `runs/20260511_153012_123456/matmul/attempt_1.s` |
| 2 | PASS | official harness exited 0; [result] PASS | `runs/20260511_153012_123456/matmul/attempt_2.s` |

### conv2d

| attempt | result | result_summary | candidate |
|---:|---|---|---|
| 1 | FAIL | official harness exited nonzero; clang assembler command failed | `runs/20260511_153012_123456/conv2d/attempt_1.s` |
| 2 | FAIL | official harness exited nonzero; failed to load symbol conv2d | `runs/20260511_153012_123456/conv2d/attempt_2.s` |
| 3 | FAIL | official harness exited nonzero; n=256 output mismatch: idx=0 | `runs/20260511_153012_123456/conv2d/attempt_3.s` |
```

## Consistency Rules

For each task, `pass@1` is true only if attempt 1 passed.

For each task, `pass@k` is true if any official attempt from 1 through `k` passed.

The `attempts` count is the number of official attempts actually evaluated for that task.

Each candidate path in `report.md` must point to the immutable attempt snapshot evaluated by the master.

Each attempt result is `PASS` if the official harness command exited with code `0`; otherwise it is `FAIL`.

`result_summary` should be a short one-line summary of the official harness result, especially the first relevant error for failed attempts.
