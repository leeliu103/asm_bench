# asm_bench

`asm_bench` runs agent benchmarks for RDNA assembly generation tasks.

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
runs/<timestamp>/prompt.md
runs/<timestamp>/report.md
runs/<timestamp>/<task_name>/attempt_N.s
```

`prompt.md` is the prompt passed to the selected agent.

`report.md` is the final benchmark report.

`attempt_N.s` files are immutable snapshots evaluated by the master.

Before launching the agent, `run_benchmark.py` removes stale `candidate.s` files for the selected tasks and clears `build/`.
