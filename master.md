# Master

You are the master agent for an RDNA assembly generation benchmark run.

## Goal

Evaluate whether subagents can generate correct RDNA assembly kernels for one or more assigned tasks.

The final output is a benchmark report with per-task results and overall `pass@1` / `pass@k` success rates.

This workflow uses iterative `pass@k`: the same task subagent may receive official failure feedback and submit revised candidates.

## Read First

Read:

```text
subagent.md
harness.py
bench_runtime.cpp
```

For each assigned task, read:

```text
tasks/<task_name>/task.py
tasks/<task_name>/template.s
```

## Attempt Definition

One attempt is one `candidate.s` file submitted by a subagent for a specific task and evaluated by the master with the official harness.

These do not count as attempts:

```text
subagent status updates
subagent questions
local edits
local harness runs
analysis without a submitted candidate
```

## pass@k Definition

For each task:

```text
pass@1 = true if attempt 1 passes
pass@k = true if any attempt from 1 through k passes
```

Across all assigned tasks:

```text
pass@1_success_rate = tasks_that_passed_on_attempt_1 / total_tasks
pass@k_success_rate = tasks_that_passed_within_k_attempts / total_tasks
```

The configured `k` is the maximum number of official attempts per task.

## Official Evaluation

For task `<task_name>`, the expected candidate path is:

```text
tasks/<task_name>/candidate.s
```

The official evaluation command is:

```bash
./harness.py --task <task_name> --candidate tasks/<task_name>/candidate.s
```

A candidate passes only if the command exits with code `0`.

Do not accept a subagent success claim without running the official harness yourself.

## Per-Task Loop

For each assigned task, run up to `k` attempts.

For each task:

1. Create a subagent for that task.
2. Instruct the subagent to follow `subagent.md`.
3. Tell the subagent the task name and candidate path:

```text
task: <task_name>
candidate: tasks/<task_name>/candidate.s
```

4. Wait for the subagent to submit `candidate.s`.
5. Count that submission as one attempt for that task.
6. Run the official harness for that task.
7. Record the result.
8. If the harness passes, stop attempts for that task.
9. If the harness fails and attempts remain, send the official failure reason back to the same subagent and ask it to continue.
10. If attempts are exhausted, mark the task as failed.

Each task has independent attempt counting.

## Multiple Tasks

You may run task subagents one at a time or in parallel.

Keep results separated by task.

Do not mix attempts from different tasks.

## Rules

Only the master decides whether an attempt passes.

While waiting for a subagent submission for a task, do not inspect that task's candidate files, run commands for that task, edit files for that task, or attempt your own solution for that task.

Do not edit candidate `.s` files yourself during the benchmark run.

Do not modify:

```text
harness.py
bench_runtime.cpp
tasks/<task_name>/task.py
tasks/<task_name>/template.s
other task definitions
```

Do not change test cases, reference logic, launch parameters, or validation code.

Only evaluate the candidate path for that task.

## Result Stages

Classify each attempt by the first failing stage, or `PASS` if all checks pass:

```text
COMPILE_FAIL       candidate did not compile to HSACO
LOAD_FAIL          HSACO did not load or the kernel symbol was missing
LAUNCH_FAIL        kernel launch or device sync failed
CORRECTNESS_FAIL   kernel ran but output validation failed
PASS               all harness checks passed
```

Use the official harness output to determine the stage.

## Final Report

At the end, write a concise benchmark report.

Include overall metrics:

```text
total_tasks:
k:
pass@1_success_rate:
pass@k_success_rate:
passed_tasks:
failed_tasks:
```

Include one section per task:

```text
task:
result:
passed_at_attempt:
pass@1:
pass@k:
final_candidate:
summary:
```

For each task, include its attempts:

```text
attempt:
candidate_path:
stage:
official_result:
change_summary:
```

`passed_at_attempt` should be `none` if no attempt passed.

`pass@1` is `true` only if attempt 1 passed.

`pass@k` is `true` if any attempt up to `k` passed.

`official_result` should summarize the relevant harness output, especially the first error or mismatch.
