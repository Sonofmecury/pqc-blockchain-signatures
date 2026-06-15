#!/usr/bin/env bash
# Build the pinned liboqs C library into ./vendor/oqs (signature algorithms only).
# Reproduces the exact crypto stack used for the published results.
# Usage:  bash scripts/setup_liboqs.sh
set -euo pipefail

LIBOQS_TAG="0.15.0"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="$ROOT/vendor/oqs"
SRC="$(mktemp -d)/liboqs"

echo "[setup] building liboqs $LIBOQS_TAG -> $PREFIX"
pip install --quiet --break-system-packages cmake ninja 2>/dev/null || pip install --quiet cmake ninja
export PATH="$HOME/.local/bin:$PATH"

git clone --depth 1 --branch "$LIBOQS_TAG" https://github.com/open-quantum-safe/liboqs.git "$SRC"
cmake -GNinja -B "$SRC/build" \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON -DOQS_USE_OPENSSL=OFF \
  -DOQS_MINIMAL_BUILD="SIG_ml_dsa_44;SIG_falcon_512;SIG_sphincs_sha2_128f_simple;SIG_sphincs_sha2_128s_simple" \
  "$SRC"
ninja -C "$SRC/build"
ninja -C "$SRC/build" install
echo "[setup] done. liboqs installed at $PREFIX/lib"
echo "[setup] now install the wrapper: pip install --break-system-packages git+https://github.com/open-quantum-safe/liboqs-python.git@0.12.0"
