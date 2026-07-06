"""
Evaluation metrics for code generation.

Metrics
-------
Pass@1
    Functional correctness: percentage of problems where the generated code
    passes all test cases (computed by evalplus externally).

AvgPassRatio (APR)
    Average ratio of test cases passed per problem (across all problems).
    Computed locally from evalplus's per-test-case output.

Usage
-----
# After running evalplus with --i-just-want-to-run-it:
python -m evalplus.evaluate --dataset humaneval \\
    --samples results/humaneval_mot.jsonl \\
    --i-just-want-to-run-it

# Then compute APR from the eval_results.json written by evalplus:
from evaluate.metrics import compute_avg_pass_ratio, load_evalplus_results
results = load_evalplus_results("humaneval_eval_results.json")
apr = compute_avg_pass_ratio(results)
print(f"APR: {apr:.1f}%")
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# AvgPassRatio
# ---------------------------------------------------------------------------


def compute_avg_pass_ratio(
    eval_results: Dict[str, Any],
    split: str = "base",
) -> float:
    """
    Compute AvgPassRatio (APR) from evalplus evaluation results.

    Parameters
    ----------
    eval_results : dict
        Parsed JSON from evalplus evaluation output (eval_results.json).
        Expected schema: { task_id: { "base": { "npass": int, "ntotal": int } } }
    split : "base" | "plus"
        Which test-case split to use for APR computation.

    Returns
    -------
    float: APR value in [0, 100] (percentage).
    """
    ratios: List[float] = []
    for task_id, result in eval_results.items():
        if split not in result:
            continue
        task_split = result[split]
        ntotal = task_split.get("ntotal", 0)
        npass = task_split.get("npass", 0)
        if ntotal > 0:
            ratios.append(npass / ntotal)

    if not ratios:
        return 0.0
    return 100.0 * sum(ratios) / len(ratios)


def load_evalplus_results(path: str) -> Dict[str, Any]:
    """
    Load evalplus evaluation results from a JSON file.

    evalplus writes a file named like ``humaneval_eval_results.json`` in the
    working directory after ``python -m evalplus.evaluate``.
    """
    with open(path) as f:
        data = json.load(f)
    # evalplus structure: {"date": ..., "eval": { task_id: { ... } }}
    if "eval" in data:
        return data["eval"]
    return data


# ---------------------------------------------------------------------------
# Pass@1 (local estimation from samples)
# ---------------------------------------------------------------------------


def compute_pass_at_1_from_jsonl(
    samples_path: str,
    groundtruth_tests: Optional[Dict[str, List[str]]] = None,
) -> float:
    """
    Estimate Pass@1 locally by running the generated code against
    a provided test-case dictionary.

    NOTE: For definitive Pass@1, always prefer running:
        python -m evalplus.evaluate --dataset <name> --samples <file>

    Parameters
    ----------
    samples_path : str
        Path to the JSONL file with generated solutions.
        Each line: {"task_id": "...", "solution": "..."}
    groundtruth_tests : dict, optional
        { task_id: [assert_statement_1, ...] }
        If None, returns None (can't evaluate locally without tests).

    Returns
    -------
    float: Pass@1 percentage, or 0.0 if groundtruth_tests is None.
    """
    if groundtruth_tests is None:
        return 0.0

    from mot.executor import execute_code

    n_total = 0
    n_pass = 0

    with open(samples_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sample = json.loads(line)
            task_id = sample.get("task_id", "")
            solution = sample.get("solution", "")
            tests = groundtruth_tests.get(task_id, [])
            n_total += 1
            if tests:
                status, _, _ = execute_code(solution, tests)
                if status == "pass":
                    n_pass += 1
            # If no groundtruth tests, count as failed (conservative)

    if n_total == 0:
        return 0.0
    return 100.0 * n_pass / n_total


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------


def print_summary(
    dataset: str,
    method: str,
    samples_path: str,
    evalplus_results_path: Optional[str] = None,
) -> None:
    """Print a concise evaluation summary."""
    n_samples = sum(
        1
        for line in Path(samples_path).read_text().splitlines()
        if line.strip()
    )
    print(f"\n{'='*55}")
    print(f"  Dataset : {dataset}")
    print(f"  Method  : {method}")
    print(f"  Samples : {n_samples}  ({samples_path})")

    if evalplus_results_path and Path(evalplus_results_path).exists():
        results = load_evalplus_results(evalplus_results_path)
        apr_base = compute_avg_pass_ratio(results, split="base")
        apr_plus = compute_avg_pass_ratio(results, split="plus")
        print(f"  APR (base) : {apr_base:.1f}%")
        print(f"  APR (plus) : {apr_plus:.1f}%")
    else:
        print("  APR        : run evalplus to compute (see README)")

    print(f"  Pass@1     : run: python -m evalplus.evaluate --dataset {dataset}")
    print(f"                      --samples {samples_path}")
    print("=" * 55)
