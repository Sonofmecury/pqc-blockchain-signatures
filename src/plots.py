"""
plots.py -- regenerate all figures from results CSVs (protocol 7.3 step 6, extended).

Layer A (primitives.csv):
    Fig 1  signature size by scheme (log bar)            -> fig1_sig_size.png
    Fig 4  trade-off: sig size vs verify time            -> fig4_tradeoff.png
Layer B (blockchain_impact.csv):
    Fig 2  transactions per block (pure schemes)         -> fig2_tx_per_block.png
    Fig 3  annual chain growth (pure schemes, log)       -> fig3_annual_growth.png
    Fig 6  hybrid vs pure transaction size               -> fig6_hybrid_tx_size.png
Sensitivity (sensitivity_blocksize.csv):
    Fig 5  block size vs throughput (Ethereum-like)      -> fig5_sensitivity.png

Run:  python3 src/plots.py
"""
from __future__ import annotations

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "..", "results")
FIGDIR = os.path.join(RESULTS, "figures")
BLUE = "#2b8cbe"; GREY = "#444444"; ORANGE = "#e6550d"


def _load(name):
    with open(os.path.join(RESULTS, name)) as f:
        return list(csv.DictReader(f))


def fig1_sig_size(rows):
    names = [r["scheme"] for r in rows]; sigs = [int(r["sig_bytes"]) for r in rows]
    colors = [GREY if r["family"] == "ECDSA" else BLUE for r in rows]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(names, sigs, color=colors); ax.set_yscale("log")
    ax.set_ylabel("Signature size (bytes, log scale)")
    ax.set_title("Figure 1. Signature size by scheme (NIST Category 1)")
    ax.tick_params(axis="x", rotation=20)
    for b, s in zip(bars, sigs):
        ax.text(b.get_x() + b.get_width() / 2, s, str(s), ha="center", va="bottom", fontsize=8)
    fig.tight_layout(); out = os.path.join(FIGDIR, "fig1_sig_size.png"); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def fig4_tradeoff(rows):
    fig, ax = plt.subplots(figsize=(8, 5))
    for r in rows:
        x, y, pk = int(r["sig_bytes"]), float(r["verify_ms_median"]), int(r["pubkey_bytes"])
        is_e = r["family"] == "ECDSA"
        ax.scatter(x, y, s=max(40, pk / 2.0), alpha=0.7, color="#d7301f" if is_e else BLUE,
                   edgecolors="black", linewidths=0.5, zorder=3)
        ax.annotate(r["scheme"], (x, y), xytext=(6, 4), textcoords="offset points", fontsize=8)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Signature size (bytes, log)"); ax.set_ylabel("Verify time (ms, median, log)")
    ax.set_title("Figure 4. Trade-off: signature size vs verify time\n(bubble area ~ public-key size; ECDSA in red)")
    ax.grid(True, which="both", ls=":", alpha=0.4)
    fig.tight_layout(); out = os.path.join(FIGDIR, "fig4_tradeoff.png"); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def _grouped(rows, value_key, title, ylabel, fname, log=False):
    chains, schemes = [], []
    for r in rows:
        if r["chain_name"] not in chains: chains.append(r["chain_name"])
        if r["scheme"] not in schemes: schemes.append(r["scheme"])
    fig, ax = plt.subplots(figsize=(9, 5)); nchain = len(chains); width = 0.8 / nchain; x = range(len(schemes))
    for ci, chain in enumerate(chains):
        vals = [next((float(r[value_key]) for r in rows if r["scheme"] == s and r["chain_name"] == chain), 0.0) for s in schemes]
        ax.bar([i + ci * width for i in x], vals, width=width, label=chain)
    if log: ax.set_yscale("log")
    ax.set_xticks([i + width * (nchain - 1) / 2 for i in x]); ax.set_xticklabels(schemes, rotation=20)
    ax.set_ylabel(ylabel); ax.set_title(title); ax.legend(fontsize=8)
    fig.tight_layout(); out = os.path.join(FIGDIR, fname); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def fig5_sensitivity(rows):
    """Block size vs throughput (Ethereum-like), one line per scheme."""
    schemes, sizes = [], []
    for r in rows:
        if r["scheme"] not in schemes: schemes.append(r["scheme"])
        mb = float(r["block_size_mb"])
        if mb not in sizes: sizes.append(mb)
    sizes.sort()
    fig, ax = plt.subplots(figsize=(8, 5))
    for s in schemes:
        ys = [next(float(r["throughput_tx_per_s"]) for r in rows if r["scheme"] == s and float(r["block_size_mb"]) == mb) for mb in sizes]
        ax.plot(sizes, ys, marker="o", label=s)
    ax.set_yscale("log"); ax.set_xlabel("Block size limit (MB)"); ax.set_ylabel("Throughput (tx/s, log)")
    ax.set_title("Figure 5. Sensitivity: throughput vs block size (Ethereum-like)")
    ax.grid(True, which="both", ls=":", alpha=0.4); ax.legend(fontsize=8)
    fig.tight_layout(); out = os.path.join(FIGDIR, "fig5_sensitivity.png"); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def fig6_hybrid(rows):
    """Hybrid vs pure transaction size on the Ethereum-like chain."""
    eth = [r for r in rows if r["chain"] == "ethereum_like"]
    order = ["ECDSA-secp256k1", "ML-DSA-44", "ECDSA+ML-DSA-44", "Falcon-512", "ECDSA+Falcon-512"]
    eth = [r for s in order for r in eth if r["scheme"] == s]
    names = [r["scheme"] for r in eth]; tx = [int(r["tx_size_bytes"]) for r in eth]
    colors = [ORANGE if r["is_hybrid"] == "True" else (GREY if r["family"] == "ECDSA" else BLUE) for r in eth]
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    bars = ax.bar(names, tx, color=colors)
    ax.set_ylabel("Transaction size (bytes)")
    ax.set_title("Figure 6. Hybrid (classical+PQ) vs pure transaction size (Ethereum-like)\norange = hybrid")
    ax.tick_params(axis="x", rotation=15)
    for b, t in zip(bars, tx):
        ax.text(b.get_x() + b.get_width() / 2, t, str(t), ha="center", va="bottom", fontsize=8)
    fig.tight_layout(); out = os.path.join(FIGDIR, "fig6_hybrid_tx_size.png"); fig.savefig(out, dpi=150); plt.close(fig)
    return out


def main():
    os.makedirs(FIGDIR, exist_ok=True); outs = []
    prims = _load("primitives.csv")
    outs += [fig1_sig_size(prims), fig4_tradeoff(prims)]
    impact_path = os.path.join(RESULTS, "blockchain_impact.csv")
    if os.path.exists(impact_path):
        impact = _load("blockchain_impact.csv")
        pure = [r for r in impact if r["is_hybrid"] == "False"]
        outs.append(_grouped(pure, "tx_per_block", "Figure 2. Transactions per block by scheme",
                             "Transactions per block", "fig2_tx_per_block.png", log=True))
        outs.append(_grouped(pure, "annual_growth_gb", "Figure 3. Annual chain growth at reference demand",
                             "Annual growth (GB/yr, log)", "fig3_annual_growth.png", log=True))
        outs.append(fig6_hybrid(impact))
    sens_path = os.path.join(RESULTS, "sensitivity_blocksize.csv")
    if os.path.exists(sens_path):
        outs.append(fig5_sensitivity(_load("sensitivity_blocksize.csv")))
    for o in outs:
        print("Wrote " + o)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
