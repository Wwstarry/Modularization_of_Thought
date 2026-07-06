#!/usr/bin/env bash
# =============================================================================
# reproduce_paper.sh
#
# Reproduces Table 1 of the MoT paper (arXiv:2503.12483).
# Runs MoT and all 6 baselines on HumanEval, HumanEval+, MBPP, MBPP+
# using GPT-4o-mini.
#
# Prerequisites:
#   export OPENAI_API_KEY="<your-key>"
#   pip install -e .                # install mot package
#
# Usage:
#   bash scripts/reproduce_paper.sh
#   bash scripts/reproduce_paper.sh --model deepseek-reasoner \
#       --base-url https://api.deepseek.com    # reproduce DeepSeek-R1 results
# =============================================================================

set -euo pipefail

# Defaults
MODEL="${MODEL:-gpt-4o-mini}"
BACKEND="${BACKEND:-openai}"
BASE_URL="${BASE_URL:-}"
OUTDIR="results"

# Parse flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)      MODEL="$2";    shift 2 ;;
        --backend)    BACKEND="$2";  shift 2 ;;
        --base-url)   BASE_URL="$2"; shift 2 ;;
        --output-dir) OUTDIR="$2";   shift 2 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

BASE_URL_ARG=""
[[ -n "$BASE_URL" ]] && BASE_URL_ARG="--base-url $BASE_URL"

echo "========================================================"
echo " MoT Paper Reproduction — Table 1"
echo " Model  : $MODEL  ($BACKEND)"
echo " Output : $OUTDIR/"
echo "========================================================"

METHODS=(mot zero_shot few_shot cot self_planning scot codecot)
HE_DATASETS=(humaneval humaneval_plus)
MB_DATASETS=(mbpp mbpp_plus)

# ---------- HumanEval family ----------
for method in "${METHODS[@]}"; do
    for ds in "${HE_DATASETS[@]}"; do
        echo ""
        echo ">>> $method on $ds"
        python evaluate/run_humaneval.py \
            --method "$method" \
            --backend "$BACKEND" \
            --model "$MODEL" \
            $BASE_URL_ARG \
            --dataset "$ds" \
            --output "$OUTDIR/${ds}_${method}.jsonl"
    done
done

# ---------- MBPP family ----------
for method in "${METHODS[@]}"; do
    for ds in "${MB_DATASETS[@]}"; do
        echo ""
        echo ">>> $method on $ds"
        python evaluate/run_mbpp.py \
            --method "$method" \
            --backend "$BACKEND" \
            --model "$MODEL" \
            $BASE_URL_ARG \
            --dataset "$ds" \
            --output "$OUTDIR/${ds}_${method}.jsonl"
    done
done

echo ""
echo "========================================================"
echo " Generation complete. Run evalplus to compute Pass@1:"
echo "========================================================"
echo ""
echo "# HumanEval:"
for method in "${METHODS[@]}"; do
    echo "  python -m evalplus.evaluate --dataset humaneval \\"
    echo "      --samples $OUTDIR/humaneval_${method}.jsonl"
done
echo ""
echo "# MBPP:"
for method in "${METHODS[@]}"; do
    echo "  python -m evalplus.evaluate --dataset mbpp \\"
    echo "      --samples $OUTDIR/mbpp_${method}.jsonl"
done
echo ""
echo "Or use scripts/eval_pass1.sh to evaluate all at once."
