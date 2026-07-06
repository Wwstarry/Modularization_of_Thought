"""
Post-process a generated JSONL file to fix remaining code extraction issues:
- Syntax errors (indented prose at start of solution)
- Trailing print/assert noise
- Invalid module imports (e.g. 'import str', 'import int')

Usage:
    python evaluate/fix_solutions.py results/humaneval_mot_gpt4omini.jsonl
"""
from __future__ import annotations
import sys, json, ast, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mot.mot_engine import _trim_to_code_start, _clean_trailing_noise

# Python builtins that should never be used as module names
_PYTHON_BUILTINS = frozenset([
    'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple', 'bytes',
    'bytearray', 'complex', 'type', 'object', 'range', 'frozenset', 'memoryview',
    'property', 'staticmethod', 'classmethod', 'super', 'zip', 'map', 'filter',
    'enumerate', 'reversed', 'sorted', 'len', 'sum', 'min', 'max', 'abs', 'round',
    'id', 'hash', 'repr', 'print', 'input', 'open', 'file',
])

_INVALID_IMPORT_RE = re.compile(
    r'^import\s+(' + '|'.join(re.escape(b) for b in _PYTHON_BUILTINS) + r')\s*$',
    re.MULTILINE,
)


def remove_invalid_imports(code: str) -> str:
    """Remove 'import <builtin>' lines that would cause ModuleNotFoundError."""
    lines = [
        line for line in code.splitlines()
        if not _INVALID_IMPORT_RE.match(line.strip())
    ]
    return "\n".join(lines)


def try_fix(solution: str) -> str:
    """Apply all fixes to a solution and return the best result."""
    fixed = _trim_to_code_start(solution)
    fixed = remove_invalid_imports(fixed)
    fixed = _clean_trailing_noise(fixed)

    # If still invalid, try removing lines from the end until it parses
    if not is_valid(fixed):
        lines = fixed.splitlines()
        for end in range(len(lines) - 1, 0, -1):
            candidate = "\n".join(lines[:end]).rstrip()
            if candidate and is_valid(candidate):
                fixed = candidate
                break

    return fixed


def is_valid(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_solutions.py <samples.jsonl>")
        sys.exit(1)

    path = Path(sys.argv[1])
    samples = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    n_fixed = 0
    n_total = len(samples)
    out_lines = []

    for s in samples:
        sol = s["solution"]
        # Always apply invalid-import removal (catches runtime errors like 'import str')
        cleaned = remove_invalid_imports(sol)
        if cleaned != sol:
            print(f"Removed invalid imports in {s['task_id']}: {len(sol)} → {len(cleaned)} chars")
            sol = cleaned
            s = dict(s, solution=sol)
            n_fixed += 1

        # Apply full fix only for syntactically invalid solutions
        if not is_valid(sol):
            fixed = try_fix(sol)
            if is_valid(fixed) and fixed != sol:
                print(f"Fixed syntax in {s['task_id']}: {len(sol)} → {len(fixed)} chars")
                s = dict(s, solution=fixed)
                n_fixed += 1
            else:
                print(f"Could not fix {s['task_id']} (still invalid)")
        out_lines.append(json.dumps(s, ensure_ascii=False))

    path.write_text("\n".join(out_lines) + "\n")
    print(f"\nFixed {n_fixed}/{n_total} solutions. Written to {path}")


if __name__ == "__main__":
    main()
