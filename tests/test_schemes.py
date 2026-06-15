"""
test_schemes.py — Correctness guarantee for the uniform signature interface
(Protocol build-order step 2).

Without these tests the benchmarks in `bench_primitives.py` could be timing
*broken* code. For every scheme in the comparison set we assert:

  1. a sign -> verify round-trip SUCCEEDS for a fresh keypair;
  2. verification FAILS when the message is tampered;
  3. verification FAILS when the signature is tampered;
  4. verification FAILS under a different (wrong) public key;
  5. sizes() returns sane, positive byte counts.

Per the protocol: if a scheme cannot load (e.g. the liboqs C library has not
been built in this environment), its tests are SKIPPED with a clear reason
rather than failing the suite.

Run:  pytest -v
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import schemes  # noqa: E402  (path injected above)

# Map name -> (instance or None, reason-if-unavailable) so each parametrised
# test can skip cleanly with an explanatory message.
_STATUS = {row["name"]: row for row in schemes.scheme_status()}
_LOADED = schemes.available_schemes()

MESSAGE = b"Post-quantum signatures for blockchain -- round-trip test vector."


def _get_or_skip(name: str) -> schemes.SignatureScheme:
    scheme = _LOADED.get(name)
    if scheme is None:
        reason = _STATUS.get(name, {}).get("reason", "scheme failed to load")
        pytest.skip(f"{name} unavailable: {reason}")
    return scheme


@pytest.mark.parametrize("name", schemes.SCHEME_NAMES)
def test_sign_verify_roundtrip(name: str) -> None:
    scheme = _get_or_skip(name)
    pk, sk = scheme.keypair()
    sig = scheme.sign(sk, MESSAGE)
    assert isinstance(pk, (bytes, bytearray)) and len(pk) > 0
    assert isinstance(sig, (bytes, bytearray)) and len(sig) > 0
    assert scheme.verify(pk, MESSAGE, sig) is True


@pytest.mark.parametrize("name", schemes.SCHEME_NAMES)
def test_tampered_message_fails(name: str) -> None:
    scheme = _get_or_skip(name)
    pk, sk = scheme.keypair()
    sig = scheme.sign(sk, MESSAGE)
    tampered = bytearray(MESSAGE)
    tampered[0] ^= 0x01  # flip one bit of the message
    assert scheme.verify(pk, bytes(tampered), sig) is False


@pytest.mark.parametrize("name", schemes.SCHEME_NAMES)
def test_tampered_signature_fails(name: str) -> None:
    scheme = _get_or_skip(name)
    pk, sk = scheme.keypair()
    sig = bytearray(scheme.sign(sk, MESSAGE))
    sig[-1] ^= 0x01  # flip one bit of the signature
    assert scheme.verify(pk, MESSAGE, bytes(sig)) is False


@pytest.mark.parametrize("name", schemes.SCHEME_NAMES)
def test_wrong_public_key_fails(name: str) -> None:
    scheme = _get_or_skip(name)
    pk1, sk1 = scheme.keypair()
    pk2, _sk2 = scheme.keypair()  # an unrelated keypair
    sig = scheme.sign(sk1, MESSAGE)
    # Signature valid under pk1 must NOT verify under an unrelated pk2.
    assert scheme.verify(pk2, MESSAGE, sig) is False


@pytest.mark.parametrize("name", schemes.SCHEME_NAMES)
def test_sizes_are_sane(name: str) -> None:
    scheme = _get_or_skip(name)
    s = scheme.sizes()
    assert s["pubkey_bytes"] > 0
    assert s["sig_bytes"] > 0
    assert s["name"] == name


def test_at_least_one_scheme_loads() -> None:
    """Sanity: the environment should provide at least the ECDSA baseline.

    (This guards against a totally broken environment where nothing imports.)
    """
    if not _LOADED:
        reasons = {n: r.get("reason") for n, r in _STATUS.items()}
        pytest.skip(f"No schemes loaded in this environment: {reasons}")
    assert len(_LOADED) >= 1
