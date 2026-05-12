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

This benchmark uses **independent pass@k**. This is the only evaluation mode
implemented in this repo.

For each task, the master launches `k` independent subagents. Each subagent
starts from the same task files, writes its own isolated candidate, may run the
local harness before submission, and submits exactly one candidate for official
evaluation.

`k` is the number of independent samples per task. `pass@1` is the result of
`agent_1` for each task. `pass@k` is true for a task if any subagent from
`agent_1` through `agent_k` passes the official harness.

This benchmark measures whether independent agents can produce a correct RDNA
assembly kernel with local testing and debugging available.

A stricter blind mode is possible but not used here:

```text
blind / no-harness pass@k
  The subagent may read the task and write a candidate, but may not run the
  harness or local checks before submission.
  This measures blind generation without feedback, but it is very strict for
  assembly kernels: small compile errors, ABI mistakes, or launch details can
  dominate the result.
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
--k       Number of independent subagents per task. Required.
--agent   Agent to launch: codex or claude. Required.
```

## Output

Each run creates:

```text
runs/<timestamp>/report.md
runs/<timestamp>/<task_name>/agent_1/candidate.s
runs/<timestamp>/<task_name>/agent_2/candidate.s
...
runs/<timestamp>/<task_name>/agent_k/candidate.s
```

Subagent directories are named `agent_1` through `agent_k`.

`report.md` is the final benchmark report.

Each `candidate.s` file is initialized from the task template and assigned to one independent subagent.

Before launching the agent, `run_benchmark.py` prepares the per-subagent
candidate directories and clears `build/`.
