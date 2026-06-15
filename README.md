# Post-Quantum Digital Signatures for Blockchain

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20703603.svg)](https://doi.org/10.5281/zenodo.20703603)

**A Performance and Storage Trade-off Analysis of ML-DSA, SLH-DSA, and Falcon versus ECDSA**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Paper 1 of the "Secure Systems in the Quantum Era" portfolio** *(flagship)*.
> The portfolio is a coordinated set of four preprints — (1) quantum-resistant
> blockchains *(this repo)*, (2) AI for blockchain security, (3) privacy-preserving
> security systems, and (4) quantum-cryptography foundations — that together
> present one coherent research identity spanning post-quantum cryptography,
> applied AI security, privacy engineering, and the quantum side.

---

## What this is

Every major blockchain (Bitcoin, Ethereum) authenticates transactions with
**ECDSA**, an elliptic-curve signature scheme that a large fault-tolerant
quantum computer breaks via Shor's algorithm. The fix is to replace ECDSA with
a NIST-standardised **post-quantum** signature scheme — but PQC signatures and
public keys are **10×–100× larger** and have very different speed profiles,
directly affecting block size, throughput, storage growth, and fees.

This project provides a **systematic, reproducible benchmark** of the three NIST
signature families against ECDSA, then **models the downstream impact** on a
blockchain: how many transactions fit in a block, how fast a node verifies them,
and how quickly the chain grows on disk. **The contribution is the four-way
comparison and the system-level analysis — not a new algorithm.**

## The four-scheme comparison (the contribution)

The four-way comparison maps the entire trade-off space and is deliberately the
core of the study — no family is dropped.

| Scheme | NIST standard | Former name | Math basis | Role in the trade-off |
|---|---|---|---|---|
| **ECDSA secp256k1** | FIPS 186-5 | — | Elliptic curves | Baseline (today's chains) |
| **ML-DSA-44** | FIPS 204 (final) | CRYSTALS-Dilithium | Module lattices | Balanced; pragmatic default |
| **Falcon-512** | FIPS 206 (**draft**) | Falcon / FN-DSA | NTRU lattices | Compact sigs; draft + side-channel caveats |
| **SLH-DSA-SHA2-128f** | FIPS 205 (final) | SPHINCS+ | Stateless hash-based | Tiny keys, huge sigs; conservative |
| *SLH-DSA-SHA2-128s* | FIPS 205 (final) | SPHINCS+ | Stateless hash-based | *(optional)* smaller sig, slower sign |

All compared at **NIST Category 1** for fairness (secp256k1's rough classical map).

> **Naming note:** ML-DSA = FIPS 204; SLH-DSA = FIPS 205; FN-DSA/Falcon = draft
> FIPS 206. ML-DSA and SLH-DSA are finalised; Falcon/FN-DSA remains **draft** as
> of 2026 — a real consideration when choosing a scheme today.

## Research questions

- **RQ1 (primitive):** keygen/sign/verify time and key/signature sizes vs ECDSA at matched security.
- **RQ2 (blockchain):** impact on (a) tx/block, (b) block verify time, (c) on-disk growth/yr.
- **RQ3 (decision):** which scheme is the best overall trade-off, and how it shifts for a high-throughput vs a store-of-value chain.

## Repository layout

```
pqc-blockchain-signatures/
├── README.md            # this file
├── LICENSE              # MIT
├── CITATION.cff         # citable (Zenodo reads this)
├── requirements.txt     # Python deps + pinned liboqs build instructions
├── Dockerfile           # pinned, reproducible build
├── config/
│   └── chains.yaml      # block sizes, intervals, overheads, tx rates
├── src/
│   ├── schemes.py           # uniform wrapper over liboqs + ECDSA  [IMPLEMENTED]
│   ├── bench_primitives.py  # Layer A: timing + sizes  [IMPLEMENTED]
│   ├── model_blockchain.py  # Layer B: tx/block/storage model  [IMPLEMENTED]
│   └── plots.py             # Figures 1-6 from results CSVs  [IMPLEMENTED]
├── results/             # primitives.csv, blockchain_impact.csv, figures/  [generated]
├── tests/
│   └── test_schemes.py  # sign→verify round-trips, tamper-detection  [IMPLEMENTED]
└── paper/               # main.md, refs.bib, table1, PDF  [DONE]
```

## Current status

Implementation and manuscript complete (build-order steps 1–7 + written paper); ready to publish.

- ✅ `src/schemes.py` — uniform `keypair() / sign() / verify() / sizes()` API over ECDSA + the three PQC families.
- ✅ `tests/test_schemes.py` — 26 tests (round-trip + tamper-detection per scheme); all pass with liboqs built.
- ✅ `src/bench_primitives.py` — primitive timing (median + IQR) → `results/primitives.csv` + `environment.json`.
- ✅ `config/chains.yaml` + `src/model_blockchain.py` — Bitcoin-like & Ethereum-like impact model → `results/blockchain_impact.csv`.
- ✅ `src/plots.py` — Figures 1–6 → `results/figures/` (incl. hybrid + sensitivity).
- ✅ `scripts/run_all.sh` + `Dockerfile` — one-command reproduction.
- ✅ `paper/main.md` + `paper/PQC_Blockchain_Preprint.pdf` — full 11-page manuscript written.

See [`STATUS.md`](STATUS.md) for the latest run's environment/install results.

## Headline results (NIST Category 1)

Measured on a 2-core x86_64 / Python 3.10 / liboqs 0.15.0 (see `results/environment.json`).
Full numbers in [`paper/table1_primitives.md`](paper/table1_primitives.md) and the CSVs.

- **PQC is not CPU-slow — the lattice scheme is faster than ECDSA.** ML-DSA-44 beats ECDSA on keygen/sign/verify; size, not speed, is the obstacle.
- **Signature size is the binding cost:** Falcon 9×, ML-DSA 34×, SLH-DSA-128s 111×, SLH-DSA-128f 241× ECDSA's 71-byte signature.
- **Blockchain impact:** replacing ECDSA cuts throughput and inflates storage growth by ~8× (Falcon) to ~100× (SLH-DSA-128f). On the Ethereum-like chain the gap is worse because ECDSA recovers the sender (`ecrecover`) and stores **no** public key, while PQC has no recovery and must carry the full key.
- **Public-key-recovery penalty (headline):** on the account chain ECDSA stores *no* public key (sender recovered via `ecrecover`); no PQC scheme can do this, so PQC must carry the full key — making migration costlier exactly where throughput is highest.
- **Hybrid is nearly free:** ECDSA+ML-DSA transactions are only ~2% larger than pure ML-DSA, so classical+PQ dual-signing during migration adds little once PQC is adopted.
- **Cost:** annual storage cost rises from ~$32–149 (ECDSA) to ~$726–3338 (ML-DSA) on the account chain at 2026 cloud prices.
- **Provisional recommendation:** ML-DSA-44 is the pragmatic drop-in; Falcon wins only where on-chain bytes dominate and slow keygen is acceptable; SLH-DSA is a conservative backup that is hard to justify for a high-throughput chain.

## Quickstart (one command)

```bash
# Option A -- Docker (builds the pinned crypto stack and runs everything)
docker build -t pqc-blockchain .
docker run --rm -v "$PWD/results:/app/results" pqc-blockchain

# Option B -- local (Linux / WSL2)
bash scripts/setup_liboqs.sh        # builds liboqs 0.15.0 into ./vendor/oqs
pip install -r requirements.txt
pip install git+https://github.com/open-quantum-safe/liboqs-python.git@0.12.0
bash scripts/run_all.sh             # tests -> benchmarks -> model -> figures
```

`run_all.sh [N] [BUDGET]` controls iterations (default 1000) and the per-op
wall-clock cap in seconds (default 12) for the slow SLH-DSA-128s signer.

## Manual setup (if not using the scripts)

### 1. Build liboqs (pinned to tag `0.15.0`)

```bash
git clone --depth 1 --branch 0.15.0 https://github.com/open-quantum-safe/liboqs
cmake -GNinja -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON \
      -DOQS_USE_OPENSSL=OFF -DCMAKE_INSTALL_PREFIX=$HOME/.local \
      -DOQS_MINIMAL_BUILD="SIG_ml_dsa_44;SIG_falcon_512;SIG_sphincs_sha2_128f_simple;SIG_sphincs_sha2_128s_simple" \
      -B build liboqs
cmake --build build && cmake --install build
export LD_LIBRARY_PATH=$HOME/.local/lib:$LD_LIBRARY_PATH
```

### 2. Python deps and run

```bash
pip install -r requirements.txt
pip install git+https://github.com/open-quantum-safe/liboqs-python.git@0.12.0
pytest -v                      # 26 tests
python src/bench_primitives.py # primitive benchmarks
python src/model_blockchain.py # blockchain impact
python src/plots.py            # figures
```

## Reproducibility

Per protocol Section 6.5: the liboqs release is **pinned (0.15.0)**; hardware and
software versions are recorded in `results/environment.json`; warm-up runs are
discarded; timings are reported as **median + IQR** (distributions are skewed);
and every PQC result is expressed as a **ratio to the ECDSA baseline** (ratios
are machine-independent and are the quotable findings). `liboqs` is a
reference/prototyping library, so absolute timings are not production-grade — the
ratios are the portable result. Pathologically slow operations are time-capped
and the **actual iteration count per op is recorded** in `primitives.csv`
(e.g. SLH-DSA-128s sign), so nothing is silently misreported.

## License

MIT — see [LICENSE](LICENSE). If you use this work, please cite it via
[`CITATION.cff`](CITATION.cff).
