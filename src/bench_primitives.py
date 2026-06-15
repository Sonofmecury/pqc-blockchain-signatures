"""
bench_primitives.py -- Layer A: primitive microbenchmarks (protocol 7.3 step 3).

For each scheme in schemes.available_schemes(), measure with perf_counter_ns
(after a discarded warm-up): keygen_ms, sign_ms, verify_ms as MEDIAN + IQR.

Iteration policy: aim for --n iterations per op, but cap any single operation by
a per-op wall-clock budget (--budget seconds) so pathologically slow signers
(e.g. SLH-DSA-128s) still finish. The ACTUAL iteration count per op is recorded
in the CSV (keygen_iters / sign_iters / verify_iters) -- honest and reproducible.

Outputs:
    results/primitives.csv      one row per scheme (Table 1 source)
    results/environment.json    hardware/software provenance

Run:  python3 src/bench_primitives.py --n 1000 --budget 12
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import schemes  # noqa: E402

NS_PER_MS = 1_000_000.0
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
MESSAGE = b"Post-quantum signatures for blockchain -- benchmark vector."


def _summ(times_ns):
    ms = sorted(t / NS_PER_MS for t in times_ns)
    n = len(ms)
    return statistics.median(ms), max(0.0, ms[(3 * n) // 4] - ms[n // 4])


def _time_op(fn, n, warmup, budget_s, min_iters=30):
    """Run fn() warmup times (discarded), then up to n times, stopping early if
    the per-op wall-clock budget is exceeded (but never below min_iters)."""
    for _ in range(warmup):
        fn()
    times = []
    start = time.perf_counter()
    for i in range(n):
        t0 = time.perf_counter_ns()
        fn()
        times.append(time.perf_counter_ns() - t0)
        if i + 1 >= min_iters and (time.perf_counter() - start) > budget_s:
            break
    return times


def bench_scheme(name, scheme, n, warmup, budget_s):
    keygen_ns = _time_op(lambda: scheme.keypair(), n, warmup, budget_s)

    pk, sk = scheme.keypair()
    sign_ns = _time_op(lambda: scheme.sign(sk, MESSAGE), n, warmup, budget_s)

    sig = scheme.sign(sk, MESSAGE)
    assert scheme.verify(pk, MESSAGE, sig) is True, name + ": sanity verify failed"
    verify_ns = _time_op(lambda: scheme.verify(pk, MESSAGE, sig), n, warmup, budget_s)

    sizes = scheme.sizes()
    kg_med, kg_iqr = _summ(keygen_ns)
    sg_med, sg_iqr = _summ(sign_ns)
    vf_med, vf_iqr = _summ(verify_ns)
    return {
        "scheme": name,
        "family": scheme.family,
        "standard": scheme.standard,
        "nist_category": scheme.nist_category,
        "draft": scheme.draft,
        "keygen_ms_median": round(kg_med, 6),
        "keygen_ms_iqr": round(kg_iqr, 6),
        "keygen_iters": len(keygen_ns),
        "sign_ms_median": round(sg_med, 6),
        "sign_ms_iqr": round(sg_iqr, 6),
        "sign_iters": len(sign_ns),
        "verify_ms_median": round(vf_med, 6),
        "verify_ms_iqr": round(vf_iqr, 6),
        "verify_iters": len(verify_ns),
        "pubkey_bytes": sizes["pubkey_bytes"],
        "sig_bytes": sizes["sig_bytes"],
    }


def _liboqs_version():
    try:
        import oqs  # type: ignore
        return str(getattr(oqs, "oqs_version", lambda: "unknown")())
    except Exception:
        return "unavailable"


def write_environment(path, n, budget_s):
    env = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "liboqs_version": _liboqs_version(),
        "target_iterations": n,
        "per_op_budget_seconds": budget_s,
        "note": "Absolute timings are machine-dependent; use ratios to ECDSA.",
    }
    with open(path, "w") as f:
        json.dump(env, f, indent=2)


def main():
    ap = argparse.ArgumentParser(description="PQC primitive microbenchmarks.")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--warmup", type=int, default=50)
    ap.add_argument("--budget", type=float, default=12.0, help="per-op wall-clock cap (s)")
    args = ap.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    loaded = schemes.available_schemes()
    if not loaded:
        print("ERROR: no schemes loaded. Build liboqs (see README).", file=sys.stderr)
        return 1

    print("Benchmarking " + str(len(loaded)) + " schemes, target n=" + str(args.n)
          + ", per-op budget=" + str(args.budget) + "s\n", flush=True)
    rows = []
    for name in schemes.SCHEME_NAMES:
        scheme = loaded.get(name)
        if scheme is None:
            print("  - " + name + ": SKIP (not loaded)", flush=True)
            continue
        print("  - " + name + ": running...", flush=True)
        rows.append(bench_scheme(name, scheme, args.n, args.warmup, args.budget))

    csv_path = os.path.join(RESULTS_DIR, "primitives.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    env_path = os.path.join(RESULTS_DIR, "environment.json")
    write_environment(env_path, args.n, args.budget)

    base = next((r for r in rows if r["scheme"].startswith("ECDSA")), rows[0])
    print("\n=== primitives summary (median ms; xECDSA in parentheses) ===")
    hdr = "{:<20}{:>18}{:>18}{:>18}{:>8}{:>9}".format(
        "scheme", "keygen", "sign", "verify", "pk B", "sig B")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        def rat(v, b):
            return "{:.4f} ({:.1f}x)".format(v, v / b) if b else "{:.4f}".format(v)
        print("{:<20}{:>18}{:>18}{:>18}{:>8}{:>9}".format(
            r["scheme"],
            rat(r["keygen_ms_median"], base["keygen_ms_median"]),
            rat(r["sign_ms_median"], base["sign_ms_median"]),
            rat(r["verify_ms_median"], base["verify_ms_median"]),
            r["pubkey_bytes"], r["sig_bytes"]))
    print("\nWrote " + csv_path)
    print("Wrote " + env_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
