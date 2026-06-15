"""
schemes.py — Uniform signature-scheme interface (Protocol build-order step 1).

Paper 1 of the "Secure Systems in the Quantum Era" portfolio:
"Post-Quantum Digital Signatures for Blockchain: A Performance and Storage
Trade-off Analysis of ML-DSA, SLH-DSA, and Falcon versus ECDSA."

This module wraps the ECDSA (secp256k1) baseline and the three NIST
post-quantum signature families behind ONE API so that the benchmark
(Layer A) and the blockchain model (Layer B) can treat every scheme
identically.

Standardised NIST names (use these throughout the paper):
  * ML-DSA   = FIPS 204 (final, Aug 2024)  -- was CRYSTALS-Dilithium
  * SLH-DSA  = FIPS 205 (final, Aug 2024)  -- was SPHINCS+
  * FN-DSA   = FIPS 206 (DRAFT, 2026)      -- was Falcon
  * ECDSA    = FIPS 186-5, curve secp256k1 -- today's blockchain baseline

Mandatory Category-1 comparison set (the four-way comparison is the
contribution; do not drop a family):
  ECDSA secp256k1 (baseline), ML-DSA-44, Falcon-512, SLH-DSA-SHA2-128f
  (optionally also SLH-DSA-SHA2-128s).

Uniform interface, per protocol Section 7.3 step 1:
  keypair()                       -> (public_key: bytes, secret_key: bytes)
  sign(secret_key, message)       -> signature: bytes
  verify(public_key, msg, sig)    -> bool
  sizes()                         -> dict with measured pubkey/sig byte sizes

Design notes:
  * Secret keys are returned/accepted as raw bytes (not opaque handles) so the
    interface is uniform and stateless across schemes. liboqs secret keys are
    exported via export_secret_key() and re-imported through the Signature
    constructor's `secret_key=` argument.
  * liboqs is a reference/prototyping library; absolute timings are not
    production-representative (see Threats to Validity, protocol Section 10).
    Report RATIOS to ECDSA, which are the machine-independent finding.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Optional dependencies. Import lazily / defensively so that a missing library
# downgrades to "scheme unavailable" (test skipped) rather than crashing the
# whole module. This matches protocol step 4: schemes that cannot load are
# skipped with a clear reason, not failed.
# ---------------------------------------------------------------------------
try:
    import oqs  # liboqs-python bindings

    _OQS_IMPORT_ERROR: Optional[str] = None
except Exception as exc:  # pragma: no cover - environment dependent
    oqs = None  # type: ignore
    _OQS_IMPORT_ERROR = repr(exc)

try:
    from coincurve import PrivateKey, PublicKey  # libsecp256k1 (Bitcoin's curve)

    _COINCURVE_IMPORT_ERROR: Optional[str] = None
except Exception as exc:  # pragma: no cover - environment dependent
    PrivateKey = None  # type: ignore
    PublicKey = None  # type: ignore
    _COINCURVE_IMPORT_ERROR = repr(exc)


def _sha256_digest(message: bytes) -> bytes:
    """Return the raw SHA-256 digest of `message`.

    coincurve's `hasher` argument expects a callable that maps message bytes ->
    digest bytes (NOT a hashlib constructor, which would return a HASH object).
    """
    return hashlib.sha256(message).digest()


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------
class SignatureScheme(ABC):
    """One uniform API over every scheme in the study."""

    #: Display name used in results/figures, e.g. "ML-DSA-44".
    name: str = "abstract"
    #: NIST standard label, e.g. "FIPS 204".
    standard: str = ""
    #: Family bucket: one of {"ECDSA", "ML-DSA", "SLH-DSA", "FN-DSA"}.
    family: str = ""
    #: NIST security category (1, 3, 5) for fair matched comparison.
    nist_category: int = 1
    #: True for schemes whose standard is still a draft (Falcon / FN-DSA).
    draft: bool = False

    @abstractmethod
    def keypair(self) -> tuple[bytes, bytes]:
        """Return (public_key, secret_key) as raw bytes."""

    @abstractmethod
    def sign(self, secret_key: bytes, message: bytes) -> bytes:
        """Sign `message` with `secret_key`; return signature bytes."""

    @abstractmethod
    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """Return True iff `signature` is valid for `message` under `public_key`."""

    def sizes(self) -> dict:
        """Measure exact public-key and signature byte sizes from a real run.

        ECDSA signatures are DER-encoded and therefore variable-length; we
        report the observed size for a representative signature. PQC schemes
        have fixed sizes.
        """
        msg = b"size-probe::secure-systems-in-the-quantum-era"
        pk, sk = self.keypair()
        sig = self.sign(sk, msg)
        return {
            "name": self.name,
            "standard": self.standard,
            "family": self.family,
            "nist_category": self.nist_category,
            "draft": self.draft,
            "pubkey_bytes": len(pk),
            "secretkey_bytes": len(sk),
            "sig_bytes": len(sig),
        }

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        flag = " (draft)" if self.draft else ""
        return f"<{self.name} [{self.standard}{flag}]>"


# ---------------------------------------------------------------------------
# ECDSA baseline (secp256k1) via coincurve / libsecp256k1
# ---------------------------------------------------------------------------
class ECDSAScheme(SignatureScheme):
    """ECDSA over secp256k1 — the signature scheme used by Bitcoin & Ethereum.

    coincurve wraps libsecp256k1 (the same C library Bitcoin Core uses), so the
    baseline is realistic rather than a generic OpenSSL curve. Signatures are
    DER-encoded (~70-72 B); public keys are stored compressed (33 B), which is
    the on-chain representation.
    """

    name = "ECDSA-secp256k1"
    standard = "FIPS 186-5"
    family = "ECDSA"
    nist_category = 1  # secp256k1 ~ 128-bit classical security; the PQC Cat-1 reference
    draft = False

    def __init__(self) -> None:
        if PrivateKey is None:
            raise RuntimeError(
                f"coincurve not available: {_COINCURVE_IMPORT_ERROR}"
            )

    def keypair(self) -> tuple[bytes, bytes]:
        priv = PrivateKey()
        secret_key = priv.secret  # 32 raw bytes
        public_key = priv.public_key.format(compressed=True)  # 33 bytes
        return public_key, secret_key

    def sign(self, secret_key: bytes, message: bytes) -> bytes:
        # coincurve hashes the message with SHA-256 (digest) and returns a
        # DER-encoded signature — exactly the blockchain convention.
        return PrivateKey(secret_key).sign(message, hasher=_sha256_digest)

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        try:
            return PublicKey(public_key).verify(
                signature, message, hasher=_sha256_digest
            )
        except Exception:
            # Malformed signature/key or verification failure -> invalid.
            return False


# ---------------------------------------------------------------------------
# Generic liboqs-backed PQC scheme
# ---------------------------------------------------------------------------
class LiboqsScheme(SignatureScheme):
    """Wrap any liboqs signature mechanism behind the uniform API.

    The concrete liboqs algorithm identifier is resolved at construction time
    from a list of candidate names, because liboqs renamed SPHINCS+ -> SLH-DSA
    across releases. The first candidate present in
    oqs.get_enabled_sig_mechanisms() wins.
    """

    def __init__(
        self,
        name: str,
        standard: str,
        family: str,
        candidate_oqs_names: list,
        nist_category: int = 1,
        draft: bool = False,
    ) -> None:
        if oqs is None:
            raise RuntimeError(f"liboqs-python not available: {_OQS_IMPORT_ERROR}")

        self.name = name
        self.standard = standard
        self.family = family
        self.nist_category = nist_category
        self.draft = draft

        enabled = set(oqs.get_enabled_sig_mechanisms())
        resolved = next((c for c in candidate_oqs_names if c in enabled), None)
        if resolved is None:
            raise RuntimeError(
                f"None of {candidate_oqs_names} are enabled in this liboqs build. "
                f"Enabled sig mechanisms: {sorted(enabled)}"
            )
        self.oqs_name = resolved

    def keypair(self) -> tuple[bytes, bytes]:
        with oqs.Signature(self.oqs_name) as signer:
            public_key = signer.generate_keypair()
            secret_key = signer.export_secret_key()
        return bytes(public_key), bytes(secret_key)

    def sign(self, secret_key: bytes, message: bytes) -> bytes:
        with oqs.Signature(self.oqs_name, secret_key=secret_key) as signer:
            return bytes(signer.sign(message))

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        try:
            with oqs.Signature(self.oqs_name) as verifier:
                return bool(verifier.verify(message, signature, public_key))
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Scheme registry — the mandatory Category-1 comparison set
# ---------------------------------------------------------------------------
@dataclass
class SchemeSpec:
    """Declarative description of a scheme to (try to) instantiate."""

    name: str
    standard: str
    family: str
    builder: object  # callable returning a SignatureScheme
    optional: bool = False  # SLH-DSA-128s is optional per the protocol
    notes: str = ""


def _spec_list() -> list:
    """The four mandatory schemes + one optional, all at NIST Category 1."""
    return [
        SchemeSpec(
            name="ECDSA-secp256k1",
            standard="FIPS 186-5",
            family="ECDSA",
            builder=lambda: ECDSAScheme(),
            notes="Baseline. Bitcoin/Ethereum signature scheme.",
        ),
        SchemeSpec(
            name="ML-DSA-44",
            standard="FIPS 204",
            family="ML-DSA",
            builder=lambda: LiboqsScheme(
                name="ML-DSA-44",
                standard="FIPS 204",
                family="ML-DSA",
                candidate_oqs_names=["ML-DSA-44", "Dilithium2"],
                nist_category=1,
                draft=False,
            ),
            notes="Module-lattice. Balanced; the pragmatic default.",
        ),
        SchemeSpec(
            name="Falcon-512",
            standard="FIPS 206 (draft)",
            family="FN-DSA",
            builder=lambda: LiboqsScheme(
                name="Falcon-512",
                standard="FIPS 206 (draft)",
                family="FN-DSA",
                candidate_oqs_names=["Falcon-512"],
                nist_category=1,
                draft=True,
            ),
            notes="NTRU-lattice. Compact sigs; draft standard; side-channel sensitive.",
        ),
        SchemeSpec(
            name="SLH-DSA-SHA2-128f",
            standard="FIPS 205",
            family="SLH-DSA",
            builder=lambda: LiboqsScheme(
                name="SLH-DSA-SHA2-128f",
                standard="FIPS 205",
                family="SLH-DSA",
                candidate_oqs_names=[
                    "SLH-DSA-SHA2-128f",
                    "SPHINCS+-SHA2-128f-simple",
                ],
                nist_category=1,
                draft=False,
            ),
            notes="Stateless hash-based. Tiny keys, huge sigs; conservative.",
        ),
        SchemeSpec(
            name="SLH-DSA-SHA2-128s",
            standard="FIPS 205",
            family="SLH-DSA",
            builder=lambda: LiboqsScheme(
                name="SLH-DSA-SHA2-128s",
                standard="FIPS 205",
                family="SLH-DSA",
                candidate_oqs_names=[
                    "SLH-DSA-SHA2-128s",
                    "SPHINCS+-SHA2-128s-simple",
                ],
                nist_category=1,
                draft=False,
            ),
            optional=True,
            notes="Optional 'small' SLH-DSA variant: smaller sig, slower sign.",
        ),
    ]


def available_schemes(include_optional: bool = True) -> dict:
    """Instantiate every scheme that can load in this environment.

    Returns a dict {name: scheme_instance}. Schemes that fail to construct
    (e.g. liboqs not built yet) are silently omitted here; use
    `scheme_status()` to see why each one is present or absent.
    """
    out: dict = {}
    for spec in _spec_list():
        if spec.optional and not include_optional:
            continue
        try:
            out[spec.name] = spec.builder()
        except Exception:
            continue
    return out


def scheme_status(include_optional: bool = True) -> list:
    """Diagnostic: for each spec, report whether it loaded and why/why not."""
    rows: list = []
    for spec in _spec_list():
        if spec.optional and not include_optional:
            continue
        row = {
            "name": spec.name,
            "standard": spec.standard,
            "family": spec.family,
            "optional": spec.optional,
            "loaded": False,
            "reason": "",
            "notes": spec.notes,
        }
        try:
            inst = spec.builder()
            row["loaded"] = True
            row["reason"] = "ok"
            if isinstance(inst, LiboqsScheme):
                row["oqs_name"] = inst.oqs_name
        except Exception as exc:
            row["reason"] = repr(exc)
        rows.append(row)
    return rows


# All scheme names in the mandatory + optional comparison set (for test params).
SCHEME_NAMES: list = [s.name for s in _spec_list()]
MANDATORY_SCHEME_NAMES: list = [s.name for s in _spec_list() if not s.optional]


if __name__ == "__main__":  # quick manual smoke test
    import json

    print("liboqs import error:", _OQS_IMPORT_ERROR)
    print("coincurve import error:", _COINCURVE_IMPORT_ERROR)
    if oqs is not None:
        print("liboqs version:", getattr(oqs, "oqs_version", lambda: "?")())
    print("\n=== scheme status ===")
    for row in scheme_status():
        print(json.dumps(row, default=str))
    print("\n=== sizes (loaded schemes) ===")
    for nm, scheme in available_schemes().items():
        try:
            print(json.dumps(scheme.sizes(), default=str))
        except Exception as exc:
            print(f"{nm}: sizes() failed: {exc!r}")
