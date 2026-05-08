import ctypes
import struct

import torch


SYMBOL = "simple_add"
BLOCK_SIZE = 256
GUARD_SIZE = 256
GUARD_VALUE = 12345.0

CASES = [
    1,
    17,
    255,
    256,
    257,
    1024,
    4096,
    10000,
]


def ceil_div(a, b):
    return (a + b - 1) // b


def pack_args(a, b, c, n):
    return struct.pack(
        "<QQQII",
        a.data_ptr(),
        b.data_ptr(),
        c.data_ptr(),
        n,
        0,
    )


def run_case(rt, n):
    torch.manual_seed(1000 + int(n))

    a = torch.randn(n, device="cuda", dtype=torch.float32)
    b = torch.randn(n, device="cuda", dtype=torch.float32)

    c_full = torch.full((n + GUARD_SIZE,), GUARD_VALUE, device="cuda", dtype=torch.float32)
    c = c_full[:n]
    guard = c_full[n:]

    expected = a + b
    torch.cuda.synchronize()

    args = pack_args(a, b, c, n)
    args_buf = ctypes.create_string_buffer(args, len(args))

    rc = rt.bench_launch(
        ceil_div(n, BLOCK_SIZE), 1, 1,
        BLOCK_SIZE, 1, 1,
        0,
        args_buf,
        len(args),
    )
    if rc != 0:
        raise RuntimeError(f"bench_launch failed for n={n}")

    if rt.bench_sync() != 0:
        raise RuntimeError(f"bench_sync failed for n={n}")

    if not torch.equal(c, expected):
        diff = (c - expected).abs()
        idx = int(torch.argmax(diff).item())
        raise AssertionError(
            f"n={n} output mismatch: "
            f"idx={idx} "
            f"expected={float(expected[idx].item())} "
            f"actual={float(c[idx].item())} "
            f"max_abs={float(diff[idx].item())}"
        )

    if not torch.equal(guard, torch.full_like(guard, GUARD_VALUE)):
        bad = torch.nonzero(guard != GUARD_VALUE).flatten()
        idx = int(bad[0].item())
        raise AssertionError(
            f"n={n} guard overwritten: "
            f"guard_offset={idx} "
            f"value={float(guard[idx].item())}"
        )
