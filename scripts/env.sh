# Shared settings for every render script. Sourced, not run.
export PYTHONHASHSEED=0          # not needed by the verified renders (see docs/DETERMINISM.md), set for safety
export MPLBACKEND=Agg
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
