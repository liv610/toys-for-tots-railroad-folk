#!/usr/bin/env bash
# The refined Moonlit Village (Phase 1) -> styles2/out/A_refined.{png,jpg,_sm.jpg}   (~20 s)
set -e; source "$(dirname "$0")/env.sh"
cd "$ROOT/styles2" && PYTHONPATH="$ROOT/styles2" python3 a2.py
