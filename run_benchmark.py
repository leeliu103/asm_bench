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


def validate_optional_dir(value, label):
    if not value:
        return None

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_dir():
        raise SystemExit(f"{label} must be a directory: {path}")
    return path.resolve()


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


def subagent_id(index):
    return f"agent_{index}"


def prepare_run_layout(run_dir, tasks, k):
    for task in tasks:
        template = TASKS_DIR / task / "template.s"
        if not template.exists():
            raise SystemExit(f"missing task template: {template}")

        for index in range(1, k + 1):
            agent_dir = run_dir / task / subagent_id(index)
            candidate = agent_dir / "candidate.s"

            try:
                agent_dir.mkdir(parents=True, exist_ok=False)
                shutil.copyfile(template, candidate)
            except OSError as exc:
                raise SystemExit(f"failed to prepare candidate {candidate}: {exc}") from exc


def build_prompt(run_dir, tasks, k, agent, isa_dir=None):
    task_list = ", ".join(tasks)
    run_id = run_dir.name
    config = [
        f"tasks: {task_list}",
        f"k: {k}",
        f"agent: {agent}",
        f"run_id: {run_id}",
        f"run_dir: {run_dir}",
    ]
    if isa_dir:
        config.append(f"isa_dir: {isa_dir}")
    config_text = "\n".join(config)

    prompt = f"""Read master.md and run the RDNA assembly generation benchmark.

Configuration:

```text
{config_text}
```

Use independent pass@k as defined in master.md.

The master/subagent/output workflow in master.md, subagent.md, and output.md is
the source of truth for evaluation.

Write the benchmark report to runs/{run_id}/report.md as described in output.md.
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
    parser.add_argument("--k", type=int, required=True, help="Number of independent subagents per task.")
    parser.add_argument(
        "--agent",
        choices=("codex", "claude"),
        required=True,
        help="Agent command to launch.",
    )
    parser.add_argument(
        "--isa-dir",
        help="Optional directory containing additional RDNA ISA knowledge for subagents.",
    )
    args = parser.parse_args()

    if args.k < 1:
        raise SystemExit("k must be >= 1")

    tasks = parse_tasks(args.tasks)
    validate_tasks(tasks)
    isa_dir = validate_optional_dir(args.isa_dir, "--isa-dir")

    run_dir = make_run_dir()
    prepare_run_layout(run_dir, tasks, args.k)
    prompt = build_prompt(run_dir, tasks, args.k, args.agent, isa_dir)
    cmd = agent_command(args.agent, prompt)

    print("Benchmark run prepared:", flush=True)
    print(f"  tasks: {', '.join(tasks)}", flush=True)
    print(f"  k: {args.k}", flush=True)
    print(f"  agent: {args.agent}", flush=True)
    print(f"  run_id: {run_dir.name}", flush=True)
    print(f"  run_dir: {run_dir}", flush=True)
    if isa_dir:
        print(f"  isa_dir: {isa_dir}", flush=True)
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
