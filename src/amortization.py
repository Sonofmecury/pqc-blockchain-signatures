"""
amortization.py -- account-model "store the public key once" analysis.

A reviewer's key objection: in an account-model chain the public key need not be
carried on every transaction; it can be stored once at first use and referenced
thereafter. This script computes, for the Ethereum-like chain, both regimes:

  first_use   : the transaction that registers the account carries the full PK
  steady_state: subsequent transactions carry only the signature (PK referenced)

It also reports the one-time storage cost of holding every account's PK once.
Result: the per-transaction PQ penalty in steady state is driven by SIGNATURE
size, not public-key size; the PK penalty is a one-time (first-use) and
migration-wave cost, not a perpetual per-tx cost.

Outputs: results/amortization.csv
Run:  python3 src/amortization.py
"""
from __future__ import annotations
import csv, os, math
import yaml

HERE=os.path.dirname(__file__); REPO=os.path.join(HERE,".."); RES=os.path.join(REPO,"results")

def main():
    prims={r["scheme"]:r for r in csv.DictReader(open(os.path.join(RES,"primitives.csv")))}
    cfg=yaml.safe_load(open(os.path.join(REPO,"config","chains.yaml")))
    ch=cfg["chains"]["ethereum_like"]; meta=cfg["meta"]
    limit=int(ch["block_size_limit_bytes"]); header=int(ch["block_header_bytes"])
    interval=float(ch["block_interval_seconds"]); overhead=int(ch["base_tx_overhead_bytes"])
    ref=float(ch["reference_tx_per_second"]); spb=int(meta["seconds_per_year"]); bpg=float(meta["bytes_per_gb"])

    order=["ECDSA-secp256k1","ML-DSA-44","Falcon-512","SLH-DSA-SHA2-128f","SLH-DSA-SHA2-128s"]
    rows=[]
    base_first=None; base_steady=None
    for name in order:
        if name not in prims: continue
        sig=int(prims[name]["sig_bytes"]); pk=int(prims[name]["pubkey_bytes"])
        is_ecdsa=prims[name]["family"]=="ECDSA"
        pk_first = 0 if is_ecdsa else pk      # ECDSA recovers sender; PQC carries PK at first use
        pk_steady = 0                          # PK stored once -> not carried thereafter
        tx_first = overhead + sig + pk_first
        tx_steady = overhead + sig + pk_steady
        def metrics(tx):
            tpb=max(0,math.floor((limit-header)/tx)); thr=tpb/interval
            growth=ref*tx*spb/bpg
            return tpb, round(thr,2), round(growth,1)
        tpb_f,thr_f,gr_f = metrics(tx_first)
        tpb_s,thr_s,gr_s = metrics(tx_steady)
        if name=="ECDSA-secp256k1": base_first=tx_first; base_steady=tx_steady
        rows.append({"scheme":name,"tx_first_use_B":tx_first,"tx_steady_state_B":tx_steady,
                     "steady_tx_xECDSA":round(tx_steady/base_steady,2),
                     "throughput_first":thr_f,"throughput_steady":thr_s,
                     "growth_first_GB_yr":gr_f,"growth_steady_GB_yr":gr_s,
                     "pk_onetime_B_per_account":pk_first})
    with open(os.path.join(RES,"amortization.csv"),"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("Ethereum-like account chain: first-use vs steady-state (PK stored once)")
    print("{:<20}{:>10}{:>12}{:>12}{:>14}{:>14}".format("scheme","txFirst","txSteady","steadyxE","thrFirst","thrSteady"))
    for r in rows:
        print("{:<20}{:>10}{:>12}{:>12}{:>14}{:>14}".format(
            r["scheme"],r["tx_first_use_B"],r["tx_steady_state_B"],str(r["steady_tx_xECDSA"])+"x",
            r["throughput_first"],r["throughput_steady"]))
    print("wrote results/amortization.csv")

if __name__=="__main__":
    raise SystemExit(main())
