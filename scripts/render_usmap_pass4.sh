#!/usr/bin/env bash
# Pass 4 U.S. map (second reference) -> usmap/out4/usmap4.{png,jpg,_sm.jpg} + animation layers in usmap/out4/anim/   (~3 min)
# Default: rebuild the scene from rules (writes out4/scene4.json).  --scene out4/scene4.json renders an edited scene.
# --width 6400 renders the same scene at 6400 x 3600 into usmap/out4_6400/ (~13 min, ~2.5 GB RAM).
# Deep-zoom viewer: python3 make_viewer4.py out4_6400 viewer4 && cp viewer4_src/index.html viewer4/
set -e; source "$(dirname "$0")/env.sh"
cd "$ROOT/usmap" && PYTHONPATH="$ROOT/folk2:$ROOT/styles2" python3 usmap4.py "$@"
