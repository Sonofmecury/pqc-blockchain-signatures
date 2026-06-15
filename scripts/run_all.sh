#!/usr/bin/env bash
# One-command reproduction of the whole study (assumes liboqs is built).
# If using the local vendor build:  bash scripts/run_all.sh
# Env: point at the liboqs install (vendor/oqs by default, else /usr/local).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -d "$ROOT/vendor/oqs/lib" ]; then
  export OQS_INSTALL_PATH="$ROOT/vendor/oqs"
  export LD_LIBRARY_PATH="$ROOT/vendor/oqs/lib:${LD_LIBRARY_PATH:-}"
fi
export PYTHONWARNINGS="ignore"

N="${1:-1000}"            # iterations (default 1000)
BUDGET="${2:-12}"         # per-op wall-clock cap seconds

echo "== 1/4 correctness tests ==";        python3 -m pytest -q --basetemp=/tmp/pqc_tmp -p no:cacheprovider
echo "== 2/4 primitive benchmarks ==";     python3 src/bench_primitives.py --n "$N" --budget "$BUDGET"
echo "== 3/4 blockchain impact model ==";  python3 src/model_blockchain.py
echo "== 4/4 figures ==";                  python3 src/plots.py
echo "Done. See results/ (CSVs + figures/) and paper/table1_primitives.md"
