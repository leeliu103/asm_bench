#!/usr/bin/env python3
import argparse
import os
import signal
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TASKS_DIR = ROOT / "tasks"
RUNS_DIR = ROOT / "runs"
BUILD_DIR = ROOT / "build"


def discover_tasks():
    if not TASKS_DIR.is_dir():
        raise SystemExit(f"missing tasks directory: {TASKS_DIR}")

    tasks = []
    for path in TASKS_DIR.iterdir():
        if not path.is_dir():
            continue
        if (path / "task.py").exists() and (path / "template.s").exists():
            tasks.append(path.name)
    return sorted(tasks)


def parse_tasks(value):
    if not value:
        return discover_tasks()
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_tasks(tasks):
    if not tasks:
        raise SystemExit("no tasks selected")

    known = set(discover_tasks())
    missing = [task for task in tasks if task not in known]
    if missing:
        known_text = ", ".join(sorted(known)) if known else "none"
        raise SystemExit(
            "unknown task(s): "
            + ", ".join(missing)
            + f" (known: {known_text})"
        )


def make_run_dir():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    run_dir = RUNS_DIR / timestamp
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise SystemExit(f"run directory already exists: {run_dir}") from exc
    except OSError as exc:
        raise SystemExit(f"failed to create run directory {run_dir}: {exc}") from exc
    return run_dir


def clean_generated_state(tasks):
    for task in tasks:
        candidate = TASKS_DIR / task / "candidate.s"
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise SystemExit(f"failed to remove stale candidate {candidate}: {exc}") from exc

    try:
        shutil.rmtree(BUILD_DIR)
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise SystemExit(f"failed to remove stale build directory {BUILD_DIR}: {exc}") from exc


def build_prompt(run_dir, tasks, k, agent):
    task_list = ", ".join(tasks)

    prompt = f"""Read master.md and run the RDNA assembly generation benchmark.

Configuration:

```text
tasks: {task_list}
k: {k}
agent: {agent}
run_dir: {run_dir}
```

Use iterative pass@k as defined in master.md.

The master/subagent/output workflow in master.md, subagent.md, and output.md is
the source of truth for evaluation.

Write benchmark outputs under the configured run_dir as described in output.md.
"""
    return prompt


def agent_command(agent, prompt):
    if agent == "codex":
        return ["codex", prompt]
    if agent == "claude":
        return ["claude", prompt]
    raise SystemExit(f"unsupported agent: {agent}")


def run_agent(cmd):
    try:
        proc = subprocess.Popen(cmd, cwd=ROOT, start_new_session=True)
    except FileNotFoundError as exc:
        raise SystemExit(f"agent command not found: {cmd[0]}") from exc
    except OSError as exc:
        raise SystemExit(f"failed to launch {cmd[0]}: {exc}") from exc

    try:
        return proc.wait()
    except KeyboardInterrupt:
        os.killpg(proc.pid, signal.SIGINT)
        try:
            return proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            return proc.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tasks",
        help="Comma-separated task names. If omitted, all task folders are used.",
    )
    parser.add_argument("--k", type=int, required=True, help="Maximum official attempts per task.")
    parser.add_argument(
        "--agent",
        choices=("codex", "claude"),
        required=True,
        help="Agent command to launch.",
    )
    args = parser.parse_args()

    if args.k < 1:
        raise SystemExit("k must be >= 1")

    tasks = parse_tasks(args.tasks)
    validate_tasks(tasks)

    run_dir = make_run_dir()
    clean_generated_state(tasks)
    prompt = build_prompt(run_dir, tasks, args.k, args.agent)
    cmd = agent_command(args.agent, prompt)

    print("Benchmark run prepared:", flush=True)
    print(f"  tasks: {', '.join(tasks)}", flush=True)
    print(f"  k: {args.k}", flush=True)
    print(f"  agent: {args.agent}", flush=True)
    print(f"  run_dir: {run_dir}", flush=True)
    print(flush=True)
    print(f"Launching {args.agent}...", flush=True)
    return run_agent(cmd)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            raise SystemExit(1) from None
        raise
