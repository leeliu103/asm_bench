#!/usr/bin/env python3
import argparse
import ctypes
import importlib
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
ROCM_PATH = Path(os.environ.get("ROCM_PATH", "/opt/rocm"))
CLANG = Path(os.environ.get("CLANG", ROCM_PATH / "llvm/bin/clang"))
HIPCC = Path(os.environ.get("HIPCC", ROCM_PATH / "llvm/bin/clang++"))


def run_cmd(cmd):
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run([str(x) for x in cmd], check=True)


def build_runtime():
    BUILD.mkdir(exist_ok=True)
    src = ROOT / "bench_runtime.cpp"
    out = BUILD / "libbench_runtime.so"

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


def build_candidate(candidate, arch):
    BUILD.mkdir(exist_ok=True)
    candidate = Path(candidate).resolve()
    out = BUILD / "candidate.hsaco"

    if not candidate.exists():
        raise FileNotFoundError(f"missing candidate asm file: {candidate}")
    if candidate.stat().st_size == 0:
        raise RuntimeError(f"{candidate} is empty")

    run_cmd([
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
    runtime_so = build_runtime()
    hsaco = build_candidate(args.candidate, args.arch)
    rt = load_runtime(runtime_so)

    try:
        if rt.bench_load(str(hsaco).encode(), task.SYMBOL.encode()) != 0:
            raise RuntimeError(f"failed to load symbol {task.SYMBOL}")

        for case in task.CASES:
            print(f"[case] {case}")
            task.run_case(rt, case)

        print("[result] PASS")
    finally:
        rt.bench_shutdown()


if __name__ == "__main__":
    main()
