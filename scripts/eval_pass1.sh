#!/usr/bin/env bash
# =============================================================================
# eval_pass1.sh
#
# Compute Pass@1 for all generated JSONL files in the results/ directory
# using evalplus.
#
# Usage:
#   bash scripts/eval_pass1.sh
#   bash scripts/eval_pass1.sh --results-dir results/
# =============================================================================

set -euo pipefail

RESULTS_DIR="${RESULTS_DIR:-results}"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --results-dir) RESULTS_DIR="$2"; shift 2 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

echo "Computing Pass@1 for all samples in $RESULTS_DIR/"
echo ""

for f in "$RESULTS_DIR"/*.jsonl; do
    [[ -e "$f" ]] || continue
    fname="$(basename "$f")"

    if [[ "$fname" == humaneval* ]]; then
        DATASET="humaneval"
    elif [[ "$fname" == mbpp* ]]; then
        DATASET="mbpp"
    else
        echo "SKIP: $fname (cannot infer dataset)"
        continue
    fi

    echo "--- $fname ($DATASET) ---"
    python -m evalplus.evaluate --dataset "$DATASET" --samples "$f"
    echo ""
done

echo "Done."
