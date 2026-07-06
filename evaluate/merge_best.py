"""
Merge solutions from multiple evaluation runs, keeping the best solution
for each problem based on:
  1. Number of doctest examples passed (higher is better)
  2. Fallback: first valid solution

Usage:
    python evaluate/merge_best.py \
        results/run1.jsonl results/run2.jsonl results/run3.jsonl \
        --output results/merged_best.jsonl
"""
from __future__ import annotations
import sys, json, ast
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mot.mot_plus import _doctest_to_asserts
from mot.executor import count_passed, execute_code
from evaluate.fix_solutions import try_fix, remove_invalid_imports, is_valid
from evalplus.data import get_human_eval_plus


def score_solution(solution: str, tests: list, timeout: int = 10) -> int:
    """Return number of doctest tests passed. -1 if invalid Python."""
    if not is_valid(solution):
        return -1
    if not tests:
        return 0  # no doctests to check
    return count_passed(solution, tests, timeout)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("runs", nargs="+", help="JSONL run files to merge")
    p.add_argument("--output", default="results/merged_best.jsonl")
    p.add_argument("--dataset", default="humaneval")
    args = p.parse_args()

    # Load problem info for doctest extraction
    if args.dataset == "humaneval":
        probs = get_human_eval_plus()
    else:
        from evalplus.data import get_mbpp_plus
        probs = get_mbpp_plus()

    # Load all runs
    all_runs = []
    for run_file in args.runs:
        samples = {
            json.loads(l)["task_id"]: json.loads(l)
            for l in Path(run_file).read_text().splitlines()
            if l.strip()
        }
        all_runs.append(samples)
        print(f"Loaded {len(samples)} samples from {run_file}")

    # Build merged results
    all_task_ids = sorted(set().union(*[set(r.keys()) for r in all_runs]))
    merged = {}
    n_improved = 0

    for tid in all_task_ids:
        p = probs.get(tid, {})
        entry = p.get("entry_point", "")
        tests = _doctest_to_asserts(p.get("prompt", ""), entry)

        # Collect all candidate solutions from all runs
        candidates = []
        for run in all_runs:
            if tid not in run:
                continue
            sol = run[tid]["solution"]
            # Apply post-processing fixes
            sol = remove_invalid_imports(sol)
            if not is_valid(sol):
                sol = try_fix(sol)
            score = score_solution(sol, tests)
            candidates.append((score, sol, run[tid]))

        if not candidates:
            continue

        # Pick the best: highest doctest score, tie-break: first valid one
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_sol, best_sample = candidates[0]

        # Check if best differs from run 1's solution
        run1_sol = remove_invalid_imports(all_runs[0].get(tid, {}).get("solution", ""))
        if best_sol != run1_sol:
            n_improved += 1
            print(f"  {tid}: improved (score {candidates[-1][0]} → {best_score})")

        merged[tid] = dict(best_sample, solution=best_sol)

    # Write merged JSONL
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for tid in sorted(merged.keys()):
            f.write(json.dumps(merged[tid], ensure_ascii=False) + "\n")

    print(f"\nMerged {len(merged)} solutions → {out_path}")
    print(f"Problems where a later run was preferred: {n_improved}")


if __name__ == "__main__":
    main()
