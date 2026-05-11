# Master

You are the master agent for an RDNA assembly generation benchmark run.

## Goal

Evaluate whether subagents can generate correct RDNA assembly kernels for one or more assigned tasks.

The final output is a benchmark report with per-task results, overall `pass@1` / `pass@k` success rates, and immutable attempt snapshots.

This workflow uses iterative `pass@k`: each task has one persistent subagent that may receive official failure feedback and submit revised candidates.

## Read First

Read:

```text
subagent.md
output.md
harness.py
bench_runtime.cpp
```

For each assigned task, read:

```text
tasks/<task_name>/task.py
tasks/<task_name>/template.s
```

## Attempt Definition

One attempt is one `candidate.s` file submitted by a subagent for a specific task, copied to an immutable attempt snapshot, and evaluated by the master with the official harness.

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

For task `<task_name>`, the subagent submits the mutable candidate path:

```text
tasks/<task_name>/candidate.s
```

Before official attempt `N`, copy the submitted candidate to an immutable attempt snapshot:

```text
runs/<run_id>/<task_name>/attempt_N.s
```

The official evaluation command evaluates the snapshot:

```bash
./harness.py --task <task_name> --candidate runs/<run_id>/<task_name>/attempt_N.s
```

A candidate passes only if the command exits with code `0`.

Do not accept a subagent success claim without running the official harness yourself.

## Per-Task Loop

For each assigned task, run up to `k` attempts using one persistent subagent.

For each task:

1. Create one `xhigh` reasoning subagent for that task.
2. Instruct the subagent to follow `subagent.md`.
3. Tell the subagent the task name and candidate path:

```text
task: <task_name>
candidate: tasks/<task_name>/candidate.s
```

4. Wait for the subagent to submit `candidate.s`.
5. Count that submission as one attempt for that task.
6. Copy `candidate.s` to `runs/<run_id>/<task_name>/attempt_N.s`.
7. Run the official harness on the attempt snapshot.
8. Record the result.
9. If the harness passes, stop attempts for that task.
10. If the harness fails and attempts remain, send the official failure reason back to the same subagent and ask it to continue.
11. If attempts are exhausted, mark the task as failed.

Each task has independent attempt counting.

Do not close, replace, or recreate the subagent for a task during the run.

## Multiple Tasks

At the start of the run, create one subagent for each assigned task, then wait for subagent responses.

Do not create extra subagents for retries, debugging, verification, or alternative solutions.

Keep results separated by task.

Do not mix attempts from different tasks.

## Rules

Only the master decides whether an attempt passes.

While waiting for subagent responses, do not inspect candidate files, run task commands, edit files, attempt your own solution, close subagents, or create additional subagents.

The master should only act when a task subagent submits `candidate.s` or asks a blocking question.

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

Only evaluate the immutable attempt snapshot for that task.

## Output

Follow `output.md` for the run output layout.

For each official attempt, create the immutable attempt snapshot before running the official harness.

At the end of the run, write `runs/<run_id>/report.md`.

The final `report.md` must use the immutable attempt snapshot paths, not the mutable `tasks/<task_name>/candidate.s` path.
