"""
Generate code solutions on MBPP / MBPP+ using MoT or any baseline method.

Usage
-----
python evaluate/run_mbpp.py \\
    --method mot \\
    --backend openai \\
    --model gpt-4o-mini \\
    --dataset mbpp \\
    --output results/mbpp_mot_gpt4omini.jsonl

# Evaluate Pass@1 with evalplus (after generation):
python -m evalplus.evaluate --dataset mbpp \\
    --samples results/mbpp_mot_gpt4omini.jsonl

The MBPP sanitized split contains 399 evaluation problems.
evalplus augments each with many additional test cases (MBPP+).

Supported methods: mot, zero_shot, few_shot, cot, self_planning, scot, codecot
"""
from __future__ import annotations

import sys
import json
import time
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mot.llm import LLMClient
from mot.mot_engine import MoTEngine
from mot.mot_plus import MoTPlusEngine
from mot.baselines import ZeroShot, FewShot, CoT, SelfPlanning, SCoT, CodeCoT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("evaluate.mbpp")

METHOD_NAMES = [
    "mot", "mot_plus",
    "zero_shot", "few_shot", "cot", "self_planning", "scot", "codecot",
]


def build_method(name: str, llm: LLMClient):
    if name == "mot":
        return MoTEngine(llm)
    if name == "mot_plus":
        return MoTPlusEngine(llm)
    if name == "zero_shot":
        return ZeroShot(llm)
    if name == "few_shot":
        return FewShot(llm)
    if name == "cot":
        return CoT(llm)
    if name == "self_planning":
        return SelfPlanning(llm)
    if name == "scot":
        return SCoT(llm)
    if name == "codecot":
        return CodeCoT(llm)
    raise ValueError(f"Unknown method: {name!r}. Choose from {METHOD_NAMES}")


def load_mbpp_problems(dataset: str) -> dict:
    """
    Load MBPP / MBPP+ via evalplus.

    evalplus's sanitized split covers 399 evaluation problems.
    """
    try:
        from evalplus.data import get_mbpp_plus  # type: ignore[import]
    except ImportError:
        logger.error("evalplus is not installed. Run: pip install evalplus")
        sys.exit(1)

    problems = get_mbpp_plus()
    return problems


def build_task_description(problem: dict) -> str:
    """
    Build the task description for an MBPP problem.

    MBPP provides: prompt (problem text + docstring), entry_point, test_list.
    We send the full prompt (which evalplus already structures nicely).
    """
    # evalplus MBPP problems have a 'prompt' field that includes the
    # function signature and docstring — exactly what we want.
    prompt = problem.get("prompt", "") or problem.get("text", "")
    return prompt.strip()


def format_solution(solution: str, problem: dict, entry_point: str) -> str:
    """
    Ensure the solution is a complete, standalone Python snippet for evalplus.

    evalplus runs the solution and then the test assertions, so we only need
    the code to define the entry-point function correctly.  We also prepend
    any import lines from the original prompt to avoid NameErrors.
    """
    solution = solution.strip()
    prompt = problem.get("prompt", "")
    import_lines = [
        ln for ln in prompt.splitlines()
        if ln.strip().startswith(("import ", "from "))
    ]
    if import_lines:
        header = "\n".join(import_lines)
        # Avoid duplicating imports that are already in the solution
        if not any(ln.strip() in solution for ln in import_lines):
            solution = header + "\n\n" + solution
    return solution


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate code solutions on MBPP / MBPP+ (MoT paper reproduction)"
    )
    p.add_argument("--method", default="mot_plus", choices=METHOD_NAMES)
    p.add_argument("--backend", default="openai", choices=["openai", "anthropic"])
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--api-key", default=None)
    p.add_argument("--base-url", default=None)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument(
        "--dataset", default="mbpp",
        choices=["mbpp", "mbpp_plus"],
        help="Dataset variant (default: mbpp)",
    )
    p.add_argument("--start-idx", type=int, default=0)
    p.add_argument("--end-idx", type=int, default=None)
    p.add_argument("--problem-id", default=None,
                   help="Run a single problem by task_id (e.g. Mbpp/2)")
    p.add_argument(
        "--output", default="results/mbpp_{method}_{model}.jsonl",
        help="Output JSONL path ({method} and {model} auto-filled).",
    )
    return p.parse_args()


def main():
    args = parse_args()

    model_slug = args.model.replace("/", "_").replace(":", "_")
    output_str = args.output.format(method=args.method, model=model_slug)
    output_path = Path(output_str)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Resumption
    existing: dict = {}
    if output_path.exists():
        with open(output_path) as f:
            for line in f:
                try:
                    s = json.loads(line)
                    existing[s["task_id"]] = s
                except Exception:
                    pass
        if existing:
            logger.info("Loaded %d existing samples from %s", len(existing), output_path)

    llm = LLMClient(
        backend=args.backend,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    method = build_method(args.method, llm)
    is_mot = args.method == "mot"

    logger.info("Loading dataset: %s", args.dataset)
    problems = load_mbpp_problems(args.dataset)
    task_ids = sorted(problems.keys())

    if args.problem_id:
        task_ids = [t for t in task_ids if t == args.problem_id]
    else:
        task_ids = task_ids[args.start_idx: args.end_idx]

    logger.info(
        "Evaluating %d problems | method=%s | model=%s/%s",
        len(task_ids), args.method, args.backend, args.model,
    )

    n_done = 0
    n_skip = 0

    with open(output_path, "a") as fout:
        for task_id in task_ids:
            problem = problems[task_id]
            entry_point = problem.get("entry_point", "")

            if task_id in existing:
                n_skip += 1
                continue

            task_desc = build_task_description(problem)
            logger.info("[%d/%d] %s (%s)", n_done + 1, len(task_ids), task_id, entry_point)

            t0 = time.time()
            mlr_graph = ""
            try:
                if is_mot:
                    code, mlr_graph = method.generate(task_desc, entry_point)
                else:
                    code = method.generate(task_desc, entry_point)
            except Exception as exc:
                logger.error("  FAILED: %s", exc)
                code = f"# Error: {exc}\ndef {entry_point}(*args, **kwargs):\n    pass"

            elapsed = time.time() - t0

            solution = format_solution(code, problem, entry_point)

            sample = {
                "task_id": task_id,
                "solution": solution,
                "mlr_graph": mlr_graph,
                "elapsed_sec": round(elapsed, 2),
            }
            fout.write(json.dumps(sample, ensure_ascii=False) + "\n")
            fout.flush()
            n_done += 1
            logger.info("  Done in %.1fs", elapsed)

    logger.info("=" * 60)
    logger.info("Evaluation complete.")
    logger.info("  Problems evaluated : %d", n_done)
    logger.info("  Problems skipped   : %d", n_skip)
    logger.info("  Output file        : %s", output_path)
    logger.info("")
    logger.info("To compute Pass@1, run:")
    logger.info("  python -m evalplus.evaluate --dataset mbpp \\")
    logger.info("      --samples %s", output_path)


if __name__ == "__main__":
    main()
