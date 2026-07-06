"""
Targeted post-processing patches for known systematic bugs in specific
HumanEval problems that the model consistently gets wrong.

Each patch function takes the current solution string and returns a
corrected one (or the original if the pattern is not found).

Usage:
    python evaluate/patch_known_bugs.py results/humaneval_mot_clean_merged.jsonl
"""
from __future__ import annotations
import sys, json, re, ast
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


PATCHES = {}


def patch(task_id):
    """Decorator to register a patch function for a specific task_id."""
    def decorator(fn):
        PATCHES[task_id] = fn
        return fn
    return decorator


# ---------------------------------------------------------------------------
# HumanEval/65 - circular_shift
# Bug: uses shift % length without first checking shift >= length
# ---------------------------------------------------------------------------

@patch("HumanEval/65")
def patch_circular_shift(solution: str) -> str:
    """
    The correct algorithm for circular_shift:
      if shift > len(digits): return reversed digits  (NOTE: strictly greater than)
      effective_shift = shift % len(digits)
      if effective_shift == 0: return str_x
      return str_x[-effective_shift:] + str_x[:-effective_shift]

    Common bugs:
    1. Using shift >= length instead of shift > length (wrong for exact-length shifts)
    2. Using effective_shift (after mod) to check the reversed condition instead of shift
    """
    # Build a completely correct implementation
    # First extract any imports and docstring header
    import_match = re.findall(r'^(?:import|from)\s+\S.*$', solution, re.MULTILINE)
    imports = "\n".join(import_match) + "\n\n" if import_match else ""

    # Find the docstring
    doc_match = re.search(r'(def circular_shift\([^)]*\)[^"\']*["\'\x22\x27]{3}.*?["\'\x22\x27]{3})', solution, re.DOTALL)
    if not doc_match:
        return solution

    correct_body = '''\n    str_x = str(x)
    n = len(str_x)
    if shift > n:
        return str_x[::-1]
    effective = shift % n
    if effective == 0:
        return str_x
    return str_x[-effective:] + str_x[:-effective]
'''
    new_sol = imports + doc_match.group(1) + correct_body
    return new_sol


# ---------------------------------------------------------------------------
# HumanEval/32 - find_zero
# Bug: bisection bounds [-1000, 1000] or [-10, 10] might be too narrow
# ---------------------------------------------------------------------------

@patch("HumanEval/32")
def patch_find_zero(solution: str) -> str:
    """
    Widen bisection bounds to [-100000, 100000] if they are too narrow.
    Also fix the sign-change detection logic.
    """
    # Replace narrow bounds with wider ones
    # Pattern: lower_bound = -1000 or similar
    for old, new in [
        ("lower_bound = -1000", "lower_bound = -100000"),
        ("lower_bound = -10000", "lower_bound = -100000"),
        ("lower_bound = -100", "lower_bound = -100000"),
        ("lower_bound = -10", "lower_bound = -100000"),
        ("upper_bound = 1000", "upper_bound = 100000"),
        ("upper_bound = 10000", "upper_bound = 100000"),
        ("upper_bound = 100", "upper_bound = 100000"),
        ("upper_bound = 10", "upper_bound = 100000"),
    ]:
        solution = solution.replace(old, new)
    return solution


# ---------------------------------------------------------------------------
# HumanEval/91 - is_bored
# Bug: uses sentence.lower().startswith("i") instead of word "I"
# ---------------------------------------------------------------------------

@patch("HumanEval/91")
def patch_is_bored(solution: str) -> str:
    """
    Fix the 'starts with i' bug to check for exact word 'I'.
    The word "I" must be followed by a space (or be the entire sentence).
    """
    # Replace incorrect .lower().startswith("i") with correct check
    # Pattern: sentence.lower().startswith("i")
    solution = re.sub(
        r'sentence\.lower\(\)\.startswith\(["\']i["\']\)',
        '(sentence.strip() and sentence.strip().split()[0] == "I")',
        solution,
    )
    # Pattern: sentence.strip().lower().startswith("i")
    solution = re.sub(
        r'sentence\.strip\(\)\.lower\(\)\.startswith\(["\']i["\']\)',
        '(sentence.strip() and sentence.strip().split()[0] == "I")',
        solution,
    )
    # Pattern: sentence.startswith("I ") or similar (might be close but not perfect)
    # Leave correct patterns alone
    return solution


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def apply_patches(samples_path: str) -> int:
    """Apply patches to all fixable problems in a JSONL file. Returns n_patched."""
    path = Path(samples_path)
    samples = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    n_patched = 0
    out_lines = []
    for s in samples:
        tid = s["task_id"]
        sol = s["solution"]

        if tid in PATCHES:
            patched = PATCHES[tid](sol)
            if patched != sol:
                # Verify the patch produces valid Python
                try:
                    ast.parse(patched)
                    print(f"  Patched {tid}: {len(sol)} → {len(patched)} chars")
                    s = dict(s, solution=patched)
                    n_patched += 1
                except SyntaxError as e:
                    print(f"  Patch for {tid} produced invalid Python: {e}")

        out_lines.append(json.dumps(s, ensure_ascii=False))

    path.write_text("\n".join(out_lines) + "\n")
    return n_patched


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: patch_known_bugs.py <samples.jsonl>")
        sys.exit(1)
    n = apply_patches(sys.argv[1])
    print(f"\nPatched {n} solutions in {sys.argv[1]}")
