#!/usr/bin/env bash
# The original Moonlit Village, exactly as approved -> village_benchmark/out/A.{png,jpg,_sm.jpg}   (~50 s)
set -e; source "$(dirname "$0")/env.sh"
cd "$ROOT/village_benchmark" && PYTHONPATH="$ROOT/village_benchmark" python3 a.py
