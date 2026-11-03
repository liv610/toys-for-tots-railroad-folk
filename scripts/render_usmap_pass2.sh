#!/usr/bin/env bash
# The current U.S. map (pass 2) -> usmap/out/usmap2.{png,jpg,_sm.jpg}   (~80 s)
set -e; source "$(dirname "$0")/env.sh"
cd "$ROOT/usmap" && PYTHONPATH="$ROOT/folk2:$ROOT/styles2" python3 usmap2.py
