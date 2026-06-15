"""
model_blockchain.py -- Layer B: blockchain impact model (protocol 7.3 step 5,
extended). Pure, deterministic functions over results/primitives.csv +
config/chains.yaml.

Per (chain, scheme) -- including HYBRID transition schemes -- derives:
  pubkey_stored_bytes, tx_size_bytes, tx_per_block, throughput_tx_per_s,
  block_verify_ms, annual_growth_gb, sustained_bandwidth_mbps,
  storage_cost_usd_yr_low/high, and x-ECDSA ratios.

Hybrids (ECDSA + PQ) model the realistic migration period: the transaction
carries BOTH a classical and a post-quantum signature (and the PQ public key).

Also writes a block-size sensitivity sweep for the Ethereum-like chain.

Outputs:
  results/blockchain_impact.csv
  results/sensitivity_blocksize.csv

Run:  python3 src/model_blockchain.py
"""
from __future__ import annotations

import csv
import math
import os

import yaml

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "..", "results")
CONFIG = os.path.join(HERE, "..", "config", "chains.yaml")
ECDSA_NAME = "ECDSA-secp256k1"


def load_primitives():
    with open(os.path.join(RESULTS, "primitives.csv")) as f:
        return {r["scheme"]: r for r in csv.DictReader(f)}


def load_cfg():
    with open(CONFIG) as f:
        return yaml.safe_load(f)


def _pk_stored(chain, scheme_name, prims):
    """Public-key bytes carried on-chain for this scheme on this chain."""
    pk = int(prims[scheme_name]["pubkey_bytes"])
    if chain.get("pubkey_always_carried", True):
        return pk
    # account chain: ECDSA recovers sender (stores nothing); PQ must carry key.
    if scheme_name == ECDSA_NAME and chain.get("ecdsa_uses_pubkey_recovery", False):
        return 0
    return pk


def _entry(chain, label, family, sig_bytes, pk_stored, verify_ms, prims, meta, costs, chain_key, is_hybrid):
    spb = int(meta["seconds_per_year"]); bpg = float(meta["bytes_per_gb"])
    limit = int(chain["block_size_limit_bytes"]); header = int(chain["block_header_bytes"])
    interval = float(chain["block_interval_seconds"]); overhead = int(chain["base_tx_overhead_bytes"])
    ref = float(chain["reference_tx_per_second"])
    tx_size = overhead + sig_bytes + pk_stored
    tx_per_block = max(0, math.floor((limit - header) / tx_size))
    throughput = tx_per_block / interval
    growth_gb = ref * tx_size * spb / bpg
    bw_mbps = ref * tx_size * 8 / 1e6  # sustained bandwidth to carry reference demand
    return {
        "chain": chain_key, "chain_name": chain["name"], "scheme": label,
        "family": family, "is_hybrid": is_hybrid,
        "sig_bytes": sig_bytes, "pubkey_stored_bytes": pk_stored,
        "tx_size_bytes": tx_size, "tx_per_block": tx_per_block,
        "throughput_tx_per_s": round(throughput, 3),
        "block_verify_ms": round(tx_per_block * verify_ms, 3),
        "reference_tx_per_s": ref,
        "annual_growth_gb": round(growth_gb, 2),
        "sustained_bandwidth_mbps": round(bw_mbps, 4),
        "storage_cost_usd_yr_low": round(growth_gb * costs["storage_usd_per_gb_year_low"], 2),
        "storage_cost_usd_yr_high": round(growth_gb * costs["storage_usd_per_gb_year_high"], 2),
    }


def model_chain(chain_key, chain, prims, meta, costs, hybrids):
    rows = []
    # pure schemes (canonical order, ECDSA first)
    for name in ["ECDSA-secp256k1", "ML-DSA-44", "Falcon-512",
                 "SLH-DSA-SHA2-128f", "SLH-DSA-SHA2-128s"]:
        if name not in prims:
            continue
        rows.append(_entry(chain, name, prims[name]["family"],
                           int(prims[name]["sig_bytes"]), _pk_stored(chain, name, prims),
                           float(prims[name]["verify_ms_median"]), prims, meta, costs,
                           chain_key, False))
    # hybrid (ECDSA + PQ) transition schemes
    e = prims[ECDSA_NAME]
    e_sig = int(e["sig_bytes"]); e_pk = _pk_stored(chain, ECDSA_NAME, prims)
    e_vf = float(e["verify_ms_median"])
    for h in hybrids:
        pq = h["pq_scheme"]
        if pq not in prims:
            continue
        pq_sig = int(prims[pq]["sig_bytes"]); pq_pk = _pk_stored(chain, pq, prims)
        pq_vf = float(prims[pq]["verify_ms_median"])
        rows.append(_entry(chain, h["name"], "Hybrid",
                           e_sig + pq_sig, e_pk + pq_pk, e_vf + pq_vf,
                           prims, meta, costs, chain_key, True))

    base = next(x for x in rows if x["scheme"] == ECDSA_NAME)
    for x in rows:
        x["tx_size_x_ecdsa"] = round(x["tx_size_bytes"] / base["tx_size_bytes"], 2)
        x["throughput_x_ecdsa"] = (round(x["throughput_tx_per_s"] / base["throughput_tx_per_s"], 3)
                                   if base["throughput_tx_per_s"] else None)
        x["growth_x_ecdsa"] = round(x["annual_growth_gb"] / base["annual_growth_gb"], 2)
    return rows


def sensitivity_blocksize(chain_key, chain, rows_for_chain, sizes_mb=(1, 2, 4, 8)):
    """Throughput vs block-size sweep, per scheme, for one chain."""
    interval = float(chain["block_interval_seconds"]); header = int(chain["block_header_bytes"])
    out = []
    for r in rows_for_chain:
        for mb in sizes_mb:
            limit = int(mb * 1_000_000)
            tpb = max(0, math.floor((limit - header) / r["tx_size_bytes"]))
            out.append({"chain": chain_key, "scheme": r["scheme"],
                        "block_size_mb": mb, "throughput_tx_per_s": round(tpb / interval, 3)})
    return out


def main():
    os.makedirs(RESULTS, exist_ok=True)
    prims = load_primitives(); cfg = load_cfg()
    meta = cfg["meta"]; costs = cfg["costs"]; hybrids = cfg.get("hybrids", [])

    all_rows, sens = [], []
    for ck, chain in cfg["chains"].items():
        rows = model_chain(ck, chain, prims, meta, costs, hybrids)
        all_rows.extend(rows)
        if ck == "ethereum_like":
            sens = sensitivity_blocksize(ck, chain, rows)

    out = os.path.join(RESULTS, "blockchain_impact.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys())); w.writeheader(); w.writerows(all_rows)
    sout = os.path.join(RESULTS, "sensitivity_blocksize.csv")
    with open(sout, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sens[0].keys())); w.writeheader(); w.writerows(sens)

    for ck, chain in cfg["chains"].items():
        rows = [r for r in all_rows if r["chain"] == ck]
        print("\n=== " + chain["name"] + " ===")
        hdr = "{:<20}{:>9}{:>10}{:>13}{:>13}{:>11}{:>14}".format(
            "scheme", "tx B", "tx/block", "thrght/s", "growth GB/yr", "BW Mbps", "$/yr (lo-hi)")
        print(hdr); print("-" * len(hdr))
        for r in rows:
            print("{:<20}{:>9}{:>10}{:>13}{:>13}{:>11}{:>14}".format(
                r["scheme"], r["tx_size_bytes"], r["tx_per_block"], r["throughput_tx_per_s"],
                r["annual_growth_gb"], r["sustained_bandwidth_mbps"],
                "{:.0f}-{:.0f}".format(r["storage_cost_usd_yr_low"], r["storage_cost_usd_yr_high"])))
    print("\nWrote " + out)
    print("Wrote " + sout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
