# asm_bench

`asm_bench` runs agent benchmarks for RDNA assembly generation tasks.

## Why This Repo Exists

State-of-the-art coding agents such as Codex and Claude Code are evolving
quickly. `asm_bench` provides a concrete benchmark for measuring their ability
to write correct RDNA assembly kernels directly. For now, the benchmark focuses
on correctness rather than performance.

The repo also supports ablation experiments: by varying the RDNA ISA knowledge
provided to the agent, we can measure how much that knowledge contributes to
correct low-level GPU assembly generation.

## Known Issues

`subagent.md` forbids using high-level languages, compiler-generated assembly,
disassembly, probe kernels, or other generated artifacts to derive a solution.
The harness does not currently enforce these restrictions. For now, the benchmark
relies on the agent's instruction-following ability.

A passing kernel may also be architecturally naive. For example, a compute-bound
GEMM task might use scalar instructions or dot-product instructions instead of
RDNA matrix instructions such as WMMA. The current benchmark is
correctness-focused, so a passing result should not be read as evidence of
performance-aware code generation.

## Evaluation Mode

This benchmark uses **iterative pass@k**. This is the only evaluation mode
implemented in this repo.

Each task is assigned to one persistent subagent. The subagent may inspect the
task files, edit the assembly candidate, run the local harness, debug failures,
and revise its solution. Local harness runs are development checks and do not
count as official attempts.

`k` is the maximum number of official submissions allowed for each task. An
official attempt happens only when the subagent submits `candidate.s` for master
evaluation (the master checks an immutable snapshot of that submission). A task
passes if any official attempt from 1 through `k` passes.

This measures whether an agent can complete a realistic assembly kernel
engineering task through testing, debugging, repair, and iteration.

There are two other possible definitions, but they are not used here:

```text
independent pass@k
  Launch k independent subagents for each task.
  Each subagent starts from the same prompt and submits one candidate.
  The task passes if any independent candidate passes.
  This is closer to traditional HumanEval-style pass@k, but less realistic for
  assembly kernel development.

blind / no-harness pass@k
  The subagent may read the task and write a candidate, but may not run the
  harness or local checks before submission.
  This measures blind generation without feedback, but is very strict and often
  dominated by small compile, ABI, or launch details.
```

Interpret `asm_bench` results as:

```text
success within k official submissions, with local debugging allowed
```

## Repository Layout

```text
run_benchmark.py       prepares a run and launches the selected master agent
master.md              master-agent benchmark protocol
subagent.md            worker-agent task instructions
output.md              required output layout and report format
harness.py             official compile/load/run/check harness
bench_runtime.cpp      HIP module loading and launch helper
```

## Run

Run all tasks:

```bash
./run_benchmark.py --k 3 --agent codex
```

Run one task:

```bash
./run_benchmark.py --tasks simple_add --k 3 --agent codex
```

Use Claude:

```bash
./run_benchmark.py --tasks simple_add --k 3 --agent claude
```

## Options

```text
--tasks   Comma-separated task names. If omitted, all tasks are used.
--k       Maximum official attempts per task. Required.
--agent   Agent to launch: codex or claude. Required.
```

## Output

Each run creates:

```text
runs/<timestamp>/report.md
runs/<timestamp>/<task_name>/attempt_N.s
```

`report.md` is the final benchmark report.

`attempt_N.s` files are immutable snapshots evaluated by the master.

Before launching the agent, `run_benchmark.py` removes stale `candidate.s` files for the selected tasks and clears `build/`.
