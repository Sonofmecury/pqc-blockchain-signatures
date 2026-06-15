# Table 1 — Primitive microbenchmarks (NIST Category 1)

Median operation time (ms) over up to 1000 iterations after warm-up; signature
and public-key sizes in bytes. Ratios are to the ECDSA-secp256k1 baseline.
Machine: 2-core x86_64, Python 3.10.12, liboqs 0.15.0 (see `results/environment.json`).
Slow operations are capped by a per-op wall-clock budget; the actual iteration
count is recorded in `results/primitives.csv` (e.g. SLH-DSA-128s sign: 47 iters).

| Scheme | Standard | Keygen ms | Sign ms | Verify ms | PubKey B | Sig B | Sig ×ECDSA |
|---|---|---:|---:|---:|---:|---:|---:|
| ECDSA-secp256k1 | FIPS 186-5 | 0.039 | 0.065 | 0.034 | 33 | 71 | 1× |
| ML-DSA-44 | FIPS 204 | 0.018 | 0.042 | 0.018 | 1312 | 2420 | 34× |
| Falcon-512 | FIPS 206 (draft) | 5.683 | 0.208 | 0.038 | 897 | 655 | 9× |
| SLH-DSA-SHA2-128f | FIPS 205 | 0.264 | 6.169 | 0.568 | 32 | 17088 | 241× |
| SLH-DSA-SHA2-128s | FIPS 205 | 16.682 | 129.124 | 0.227 | 32 | 7856 | 111× |

## Key findings (Layer A)

1. **CPU time is NOT the obstacle for the lattice schemes.** ML-DSA-44 is
   actually *faster* than ECDSA on all three operations (keygen 0.5×, sign 0.6×,
   verify 0.5×). This refutes the intuition that post-quantum = slow.

2. **Signature size is the real cost.** Every PQC signature is far larger than
   ECDSA's 71 bytes: Falcon 9×, ML-DSA 34×, SLH-DSA-128s 111×, SLH-DSA-128f 241×.
   For a blockchain — where every signature is stored permanently and gossiped to
   every node — this is the binding constraint (supports hypothesis H2).

3. **Each family has a distinct pathology:**
   - *Falcon* has the smallest PQC signature (655 B) but a very slow, variable
     keygen (147× ECDSA) and is side-channel sensitive + still draft (FIPS 206).
   - *ML-DSA* is the balanced, pragmatic default — fast everywhere, moderate
     2420 B signature.
   - *SLH-DSA* has tiny 32 B keys but punishing signatures: the 'f' variant is
     huge (17 KB), the 's' variant signs ~2000× slower than ECDSA.

4. **Provisional recommendation (to be confirmed by the blockchain model):**
   ML-DSA-44 is the practical drop-in; Falcon is attractive only where on-chain
   bytes dominate and a slow signer is acceptable; SLH-DSA is a conservative
   backup whose cost is hard to justify for high-throughput chains.

Figures: `results/figures/fig1_sig_size.png` (signature sizes),
`results/figures/fig4_tradeoff.png` (size vs verify-time trade-off).
