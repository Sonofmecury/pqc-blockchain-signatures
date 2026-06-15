# STATUS — Implementation complete (build-order steps 1–7)

**Project:** Post-Quantum Digital Signatures for Blockchain — *Paper 1 of the
"Secure Systems in the Quantum Era" portfolio (flagship, 9.5/10).*
**Updated:** 2026-06-13 (steps 3–7 completed interactively; liboqs built into `vendor/`).
**Remaining:** write the manuscript (`paper/main.md`), then publish (Zenodo DOI → TechRxiv).

---

## 1. Build-order progress (protocol Section 7.3)

| Step | Component | State |
|---|---|---|
| 1 | `src/schemes.py` — uniform API over ECDSA + 3 PQC families | ✅ done |
| 2 | `tests/test_schemes.py` — 26 tests | ✅ all pass (liboqs built) |
| 3 | `src/bench_primitives.py` — primitive timing → primitives.csv | ✅ done |
| 4 | `config/chains.yaml` — two chain models, documented constants | ✅ done |
| 5 | `src/model_blockchain.py` — impact model → blockchain_impact.csv | ✅ done |
| 6 | `src/plots.py` — Figures 1–4 | ✅ done |
| 7 | `scripts/run_all.sh` + `setup_liboqs.sh` + Dockerfile + README | ✅ done |
| — | `paper/main.md` manuscript | ⬜ next |

## 2. Requirements review (against protocol objectives)

**RQ1 — primitive comparison:** ✅ keygen/sign/verify (median+IQR) and key/sig
sizes for all four schemes at NIST Category 1 → `results/primitives.csv`, Table 1.

**RQ2 — blockchain impact:** ✅ tx size, tx/block, throughput, block-verify time,
annual storage growth for two chain models → `results/blockchain_impact.csv`.

**RQ3 — decision:** ✅ provisional recommendation (ML-DSA-44 pragmatic; Falcon for
byte-constrained; SLH-DSA conservative backup) supported by the data; contrast
between store-of-value and high-throughput chains captured.

**Metrics (Section 6.3):** ✅ all defined metrics implemented; ratios-to-ECDSA reported.

**Two chain models (Section 6.4):** ✅ Bitcoin-like (UTXO, key always carried) and
Ethereum-like (account; ECDSA `ecrecover` ⇒ no key stored, PQC must carry key).
The pubkey-recovery asymmetry is implemented and surfaced — a key finding.

**Fairness / rigor (Section 6.5):** ✅ warm-up discarded; median+IQR; liboqs pinned
0.15.0; environment.json provenance; slow ops time-capped with the **actual
iteration count recorded** (honest, not silently truncated).

**Reproducibility (Section 7.3 step 7):** ✅ `scripts/setup_liboqs.sh` (builds the
pinned lib), `scripts/run_all.sh` (tests→bench→model→plots), Dockerfile entrypoint
runs the whole pipeline; README quickstart documents both paths.

**Figures/tables:** ✅ Table 1 (`paper/table1_primitives.md`); Fig 1 (sig size),
Fig 2 (tx/block), Fig 3 (annual growth), Fig 4 (trade-off) in `results/figures/`.

## 3. Headline numbers (NIST Cat 1; 2-core x86_64, liboqs 0.15.0)

Primitive: ML-DSA-44 is *faster* than ECDSA on all ops (0.5–0.6×); Falcon keygen
is ~147× ECDSA; SLH-DSA-128s sign ~1985× ECDSA. Signature size is the cost:
Falcon 9×, ML-DSA 34×, SLH-DSA-128s 111×, SLH-DSA-128f 241× ECDSA's 71 B.

Blockchain (Ethereum-like, account): throughput drops from 913 tx/s (ECDSA) to
41 (ML-DSA), 94 (Falcon), 9 (SLH-DSA-128f); annual growth rises from ~0.5 TB to
12 TB (ML-DSA) and 54 TB (SLH-DSA-128f) at the reference demand rate.

## 4. Known limitations (carry into the paper's Threats to Validity)

- liboqs is a reference library; absolute timings aren't production-grade — ratios are the portable result.
- SLH-DSA-128s sign/keygen medians are over fewer iterations (time-capped); re-run overnight at full N for the camera-ready.
- The blockchain model is first-order (no mempool/network/consensus dynamics); the Ethereum byte-budget is an abstraction of gas accounting. Documented in `chains.yaml`.
- Falcon/FN-DSA is draft (FIPS 206) and side-channel sensitive — a real adoption caveat, not a code issue.

## 5. Next steps

1. Write `paper/main.md` (6–9 pp) from these results: Intro → Background/Related Work → Methodology → Implementation → Results (Table 1 + Figs 1–4) → Discussion (answer RQ3, revisit H1–H3) → Threats → Conclusion.
2. Expand `paper/refs.bib` to 15–25 references (NIST FIPS 203/204/205, OQS, PQC-benchmarking and quantum-safe-blockchain literature).
3. Overnight full-N benchmark re-run for camera-ready numbers.
4. Publish: GitHub → Zenodo (DOI) → TechRxiv (+ arXiv if endorsed). Register ORCID first.
