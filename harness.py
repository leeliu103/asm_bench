#!/usr/bin/env python3
import argparse
import ctypes
import importlib
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ROCM_PATH = Path(os.environ.get("ROCM_PATH", "/opt/rocm"))
CLANG = Path(os.environ.get("CLANG", ROCM_PATH / "llvm/bin/clang"))
HIPCC = Path(os.environ.get("HIPCC", ROCM_PATH / "llvm/bin/clang++"))


def run_cmd(cmd):
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], check=True)


def run_cmd_capture(cmd):
    print("+", " ".join(str(x) for x in cmd))
    proc = subprocess.run(
        [str(x) for x in cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc.returncode


def resolve_candidate(candidate):
    candidate = Path(candidate).resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"missing candidate asm file: {candidate}")
    if candidate.stat().st_size == 0:
        raise RuntimeError(f"{candidate} is empty")
    return candidate


def candidate_build_dir(candidate):
    return candidate.parent / "build"


def build_runtime(build_dir):
    build_dir.mkdir(parents=True, exist_ok=True)
    src = ROOT / "bench_runtime.cpp"
    out = build_dir / "libbench_runtime.so"

    run_cmd([
        HIPCC,
        "-shared",
        "-fPIC",
        "-O2",
        "-o",
        out,
        src,
        f"-I{ROCM_PATH / 'include'}",
        f"-L{ROCM_PATH / 'lib'}",
        f"-Wl,-rpath,{ROCM_PATH / 'lib'}",
        "-lamdhip64",
        "-D__HIP_PLATFORM_AMD__",
    ])
    return out


def build_candidate(candidate, arch, build_dir):
    build_dir.mkdir(parents=True, exist_ok=True)
    out = build_dir / "candidate.hsaco"

    rc = run_cmd_capture([
        CLANG,
        "-x",
        "assembler",
        "-target",
        "amdgcn-amd-amdhsa",
        f"-mcpu={arch}",
        "-o",
        out,
        candidate,
    ])
    if rc != 0:
        raise RuntimeError(f"candidate compile failed with exit code {rc}")
    return out


def load_runtime(runtime_so):
    hip_lib = ROCM_PATH / "lib/libamdhip64.so"
    ctypes.CDLL(str(hip_lib if hip_lib.exists() else "libamdhip64.so"), mode=ctypes.RTLD_GLOBAL)
    rt = ctypes.CDLL(str(runtime_so))

    rt.bench_init.restype = ctypes.c_int

    rt.bench_load.restype = ctypes.c_int
    rt.bench_load.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

    rt.bench_launch.restype = ctypes.c_int
    rt.bench_launch.argtypes = [
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_size_t,
    ]

    rt.bench_sync.restype = ctypes.c_int
    rt.bench_shutdown.restype = None

    if rt.bench_init() != 0:
        raise RuntimeError("bench_init failed")
    return rt


def load_task(name):
    task = importlib.import_module(f"tasks.{name}.task")
    for attr in ("SYMBOL", "CASES", "run_case"):
        if not hasattr(task, attr):
            raise RuntimeError(f"task {name} missing required attribute {attr}")
    return task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True, help="Task module name, e.g. simple_add")
    parser.add_argument("--candidate", required=True, help="Path to candidate .s file")
    parser.add_argument("--arch", default=os.environ.get("GPU_ARCH", "gfx1201"))
    args = parser.parse_args()

    task = load_task(args.task)
    try:
        candidate = resolve_candidate(args.candidate)
    except Exception as exc:
        print(f"[error] {exc}")
        print("[result] COMPILE_ERROR")
        raise SystemExit(1)

    build_dir = candidate_build_dir(candidate)
    runtime_so = build_runtime(build_dir)

    try:
        hsaco = build_candidate(candidate, args.arch, build_dir)
    except Exception as exc:
        print(f"[error] {exc}")
        print("[result] COMPILE_ERROR")
        raise SystemExit(1)

    rt = load_runtime(runtime_so)

    try:
        if rt.bench_load(str(hsaco).encode(), task.SYMBOL.encode()) != 0:
            raise RuntimeError(f"failed to load symbol {task.SYMBOL}")

        failed_cases = 0
        for case in task.CASES:
            try:
                task.run_case(rt, case)
            except AssertionError as exc:
                failed_cases += 1
                print(f"[case] {case} FAIL: {exc}")
            else:
                print(f"[case] {case} PASS")

        if failed_cases:
            print(f"[result] TEST_FAIL failed_cases={failed_cases}/{len(task.CASES)}")
            raise SystemExit(1)

        print("[result] PASS")
    finally:
        rt.bench_shutdown()


if __name__ == "__main__":
    main()
