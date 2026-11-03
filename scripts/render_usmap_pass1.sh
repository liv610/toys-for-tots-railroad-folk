#!/usr/bin/env bash
# The first U.S. map reconstruction -> usmap/out/usmap.{png,jpg,_sm.jpg}   (~70 s)
set -e; source "$(dirname "$0")/env.sh"
cd "$ROOT/usmap" && PYTHONPATH="$ROOT/folk2:$ROOT/styles2" python3 usmap.py
