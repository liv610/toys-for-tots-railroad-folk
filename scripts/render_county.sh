#!/usr/bin/env bash
# The county expansion test -> county/out/county.{png,jpg,_sm.jpg}   (~20 s)
# county.py hard-codes an absolute save path from the original machine; this runs it unmodified
# but redirects that one save call in memory to the project's county/out folder.
set -e; source "$(dirname "$0")/env.sh"
mkdir -p "$ROOT/county/out"
cd "$ROOT/county" && PYTHONPATH="$ROOT/styles2" python3 - <<PY
src = open('county.py').read().replace("c.save('/home/claude/county/out/county')", "c.save('$ROOT/county/out/county')")
exec(compile(src, 'county.py', 'exec'), {'__name__': '__main__'})
PY
