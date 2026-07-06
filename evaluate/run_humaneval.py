"""
Generate code solutions on HumanEval / HumanEval+ / HumanEval-ET using MoT
or any of the six baseline prompting methods.

Usage
-----
python evaluate/run_humaneval.py \\
    --method mot \\
    --backend openai \\
    --model gpt-4o-mini \\
    --dataset humaneval \\
    --output results/humaneval_mot_gpt4omini.jsonl

# Evaluate Pass@1 with evalplus (after generation):
python -m evalplus.evaluate --dataset humaneval \\
    --samples results/humaneval_mot_gpt4omini.jsonl

Supported methods: mot, zero_shot, few_shot, cot, self_planning, scot, codecot
Supported datasets: humaneval, humaneval_plus (evalplus provides both)

Notes
-----
- Supports resumption: already-completed task_ids are skipped.
- Each output line: { "task_id": ..., "solution": ..., "mlr_graph": ...,
                      "elapsed_sec": ... }
  (mlr_graph is empty string for non-MoT methods)
"""
from __future__ import annotations

import sys
import json
import time
import logging
import argparse
from pathlib import Path

# Allow running from project root or evaluate/ subdirectory
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
logger = logging.getLogger("evaluate.humaneval")

# ---------------------------------------------------------------------------
# Method registry
# ---------------------------------------------------------------------------

METHOD_NAMES = [
    "mot", "mot_plus",
    "zero_shot", "few_shot", "cot", "self_planning", "scot", "codecot",
]


def build_method(name: str, llm: LLMClient):
    """Instantiate the requested prompting method."""
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


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------


def load_humaneval_problems(dataset: str) -> dict:
    """
    Load HumanEval or HumanEval+ problems via evalplus.

    evalplus provides both variants through get_human_eval_plus():
    - 'humaneval'      : original 164 problems (base test cases only)
    - 'humaneval_plus' : original 164 problems (with extended test cases)
    """
    try:
        from evalplus.data import get_human_eval_plus  # type: ignore[import]
    except ImportError:
        logger.error(
            "evalplus is not installed. Run: pip install evalplus"
        )
        sys.exit(1)

    problems = get_human_eval_plus()
    return problems


def build_task_description(problem: dict) -> str:
    """Return the task description string for a HumanEval problem."""
    return problem.get("prompt", "").strip()


def format_solution(solution: str, problem: dict) -> str:
    """
    Prepend import lines from the problem prompt so evalplus can run the code.
    """
    prompt = problem.get("prompt", "")
    import_lines = [
        ln for ln in prompt.splitlines()
        if ln.strip().startswith(("import ", "from "))
    ]
    if import_lines:
        return "\n".join(import_lines) + "\n\n" + solution.strip()
    return solution.strip()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate code solutions on HumanEval / HumanEval+ (MoT paper reproduction)"
    )
    # Method
    p.add_argument(
        "--method", default="mot_plus", choices=METHOD_NAMES,
        help="Prompting method (default: mot_plus)",
    )
    # LLM backend
    p.add_argument(
        "--backend", default="openai", choices=["openai", "anthropic"],
        help="LLM backend (default: openai)",
    )
    p.add_argument("--model", default="gpt-4o-mini",
                   help="Model name (default: gpt-4o-mini)")
    p.add_argument("--api-key", default=None,
                   help="API key (falls back to env vars)")
    p.add_argument("--base-url", default=None,
                   help="Custom API base URL (for DeepSeek, local servers, etc.)")
    p.add_argument("--temperature", type=float, default=1.0,
                   help="Sampling temperature (default: 1.0, matches paper)")
    p.add_argument("--max-tokens", type=int, default=4096,
                   help="Max tokens per generation (default: 4096)")
    # Dataset
    p.add_argument(
        "--dataset", default="humaneval",
        choices=["humaneval", "humaneval_plus"],
        help="Dataset variant (default: humaneval)",
    )
    # Range / filter
    p.add_argument("--start-idx", type=int, default=0,
                   help="Start from this problem index (for resumption)")
    p.add_argument("--end-idx", type=int, default=None,
                   help="Stop after this problem index (exclusive)")
    p.add_argument("--problem-id", default=None,
                   help="Run a single problem by task_id (e.g. HumanEval/0)")
    # Output
    p.add_argument(
        "--output", default="results/humaneval_{method}_{model}.jsonl",
        help=(
            "Output JSONL path. {method} and {model} are auto-filled. "
            "(default: results/humaneval_{method}_{model}.jsonl)"
        ),
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    args = parse_args()

    # Resolve output path
    model_slug = args.model.replace("/", "_").replace(":", "_")
    output_str = args.output.format(method=args.method, model=model_slug)
    output_path = Path(output_str)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing samples (for resumption)
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

    # Build LLM client
    llm = LLMClient(
        backend=args.backend,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    # Build method
    method = build_method(args.method, llm)
    is_mot = args.method == "mot"

    # Load dataset
    logger.info("Loading dataset: %s", args.dataset)
    problems = load_humaneval_problems(args.dataset)
    task_ids = sorted(problems.keys())

    # Filter range / single problem
    if args.problem_id:
        task_ids = [t for t in task_ids if t == args.problem_id]
    else:
        task_ids = task_ids[args.start_idx: args.end_idx]

    logger.info(
        "Evaluating %d problems | method=%s | model=%s/%s",
        len(task_ids), args.method, args.backend, args.model,
    )

    # Main loop
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

            # Format for evalplus (prepend imports)
            solution = format_solution(code, problem)

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

    # Summary
    logger.info("=" * 60)
    logger.info("Evaluation complete.")
    logger.info("  Problems evaluated : %d", n_done)
    logger.info("  Problems skipped   : %d", n_skip)
    logger.info("  Output file        : %s", output_path)
    logger.info("")
    logger.info("To compute Pass@1, run:")
    logger.info("  python -m evalplus.evaluate --dataset humaneval \\")
    logger.info("      --samples %s", output_path)


if __name__ == "__main__":
    main()
