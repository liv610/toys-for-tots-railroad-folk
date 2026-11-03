#!/usr/bin/env bash
# Pass 3 U.S. map -> usmap/out/usmap3.{png,jpg,_sm.jpg} plus animation layers in usmap/out/anim/   (~2.5 min)
# Default: rebuild the scene from rules (writes out/scene3.json).  With --scene out/scene3.json: render an edited scene file.
set -e; source "$(dirname "$0")/env.sh"
cd "$ROOT/usmap" && PYTHONPATH="$ROOT/folk2:$ROOT/styles2" python3 usmap3.py "$@"
