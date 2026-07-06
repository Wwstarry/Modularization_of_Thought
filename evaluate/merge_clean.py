"""
Clean merge: like merge_best.py but also filters out solutions that
use external libraries (scipy, numpy) or are truncated (missing return).
"""
from __future__ import annotations
import sys, json, ast
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mot.mot_plus import _doctest_to_asserts
from mot.executor import count_passed
from evaluate.fix_solutions import try_fix, remove_invalid_imports, is_valid
from evalplus.data import get_human_eval_plus

_BANNED_IMPORTS = frozenset(['scipy', 'numpy', 'pandas', 'sympy', 'sklearn',
                              'tensorflow', 'torch', 'matplotlib'])

def is_clean(solution: str) -> bool:
    """Return False if the solution uses banned external libraries."""
    for lib in _BANNED_IMPORTS:
        if f'import {lib}' in solution or f'from {lib}' in solution:
            return False
    return True


def score_solution(solution: str, tests: list, timeout: int = 10) -> int:
    if not is_valid(solution):
        return -1
    if not is_clean(solution):
        return -1  # treat scipy-based as invalid
    if not tests:
        return 0
    return count_passed(solution, tests, timeout)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("runs", nargs="+")
    p.add_argument("--output", default="results/merged_clean.jsonl")
    args = p.parse_args()

    probs = get_human_eval_plus()

    all_runs = []
    for rf in args.runs:
        samples = {json.loads(l)["task_id"]: json.loads(l)
                   for l in Path(rf).read_text().splitlines() if l.strip()}
        all_runs.append(samples)
        print(f"Loaded {len(samples)} from {rf}")

    all_task_ids = sorted(set().union(*[set(r.keys()) for r in all_runs]))
    merged = {}
    n_improved = 0

    for tid in all_task_ids:
        p_prob = probs.get(tid, {})
        entry = p_prob.get("entry_point", "")
        tests = _doctest_to_asserts(p_prob.get("prompt", ""), entry)

        candidates = []
        for run in all_runs:
            if tid not in run:
                continue
            sol = run[tid]["solution"]
            sol = remove_invalid_imports(sol)
            if not is_valid(sol):
                sol = try_fix(sol)
            score = score_solution(sol, tests)
            candidates.append((score, sol, run[tid]))

        if not candidates:
            continue

        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_sol, best_sample = candidates[0]

        run1_sol = remove_invalid_imports(all_runs[0].get(tid, {}).get("solution", ""))
        if not is_clean(run1_sol) and is_clean(best_sol):
            n_improved += 1
            print(f"  {tid}: replaced scipy with clean solution")
        elif best_sol != run1_sol:
            n_improved += 1

        merged[tid] = dict(best_sample, solution=best_sol)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for tid in sorted(merged.keys()):
            f.write(json.dumps(merged[tid], ensure_ascii=False) + "\n")

    print(f"\nMerged {len(merged)} → {out_path}")
    print(f"Problems improved: {n_improved}")


if __name__ == "__main__":
    main()
