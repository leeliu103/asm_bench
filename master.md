# Master

You are the master agent for an RDNA assembly generation benchmark run.

## Goal

Evaluate whether independent subagents can generate correct RDNA assembly kernels for one or more assigned tasks.

The final output is a benchmark report with per-subagent results and overall `pass@1` / `pass@k` success rates.

This workflow uses independent `pass@k`: each task has `k` independent subagents. Each subagent submits exactly one candidate for official evaluation.

Subagents may run the local harness before submission, but each subagent gets only one official evaluation.

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

## Submission Definition

One submission is one `candidate.s` file produced by one subagent for one task and evaluated by the master with the official harness.

These do not count as official submissions:

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
pass@1 = true if agent_1 passes
pass@k = true if any subagent from agent_1 through agent_k passes
```

Across all assigned tasks:

```text
pass@1_success_rate = tasks_where_agent_1_passed / total_tasks
pass@k_success_rate = tasks_where_any_subagent_passed / total_tasks
```

The configured `k` is the number of independent subagents per task.
Subagent IDs are `agent_1` through `agent_k`, ordered by numeric suffix.

## Official Evaluation

For task `<task_name>` and subagent `<subagent_id>`, the assigned candidate path is:

```text
runs/<run_id>/<task_name>/<subagent_id>/candidate.s
```

The official evaluation command evaluates that submitted candidate:

```bash
./harness.py --task <task_name> --candidate runs/<run_id>/<task_name>/<subagent_id>/candidate.s
```

A candidate is `success` only if the command exits with code `0`; otherwise it is `failure`.

Do not accept a subagent success claim without running the official harness yourself.

## Per-Task Loop

For each assigned task, run exactly `k` independent subagents.

For each task:

1. Create `k` independent `xhigh` reasoning subagents for that task.
2. Assign subagent IDs `agent_1` through `agent_k`.
3. Instruct each subagent to follow `subagent.md`.
4. Tell each subagent the run ID, task name, subagent ID, candidate path, and optional ISA directory:

```text
run_id: <run_id>
task: <task_name>
subagent_id: <subagent_id>
candidate: runs/<run_id>/<task_name>/<subagent_id>/candidate.s
isa_dir: <isa_dir, if provided>
```

Omit `isa_dir` if it is not provided in the run configuration.

5. Wait for each subagent to submit its assigned `candidate.s`.
6. Run the official harness once for each submitted candidate.
7. Record `success` or `failure` for that task and subagent.
8. Close the subagent after its official evaluation.

Each subagent gets one official evaluation.

Do not ask a subagent to revise after official evaluation.

## Multiple Tasks

At the start of the run, create `k` subagents for each assigned task, then wait for subagent responses.

Do not create extra subagents for retries, debugging, verification, or alternative solutions.

Keep results separated by task and subagent ID.

Do not mix submissions from different tasks or subagents.

## Rules

Only the master decides whether a candidate passes.

Do not inspect a subagent's candidate, run task commands for it, edit files, or attempt your own solution before that subagent submits.

Do not create additional subagents beyond the configured `k` per task.

The master should only act when a subagent submits `candidate.s` or asks a blocking question.

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

Only evaluate the candidate path assigned to that task and subagent.

## Output

Follow `output.md` for the run output layout.

At the end of the run, write `runs/<run_id>/report.md`.
