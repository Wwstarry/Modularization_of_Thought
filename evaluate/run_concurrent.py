"""
Concurrent evaluation script for MoT / MoT+ on HumanEval / MBPP.

Uses ThreadPoolExecutor to run multiple LLM calls in parallel,
reducing wall-clock time from ~40min to ~5-8min for HumanEval.

Usage
-----
HTTPS_PROXY=http://10.229.18.30:8412 \\
python evaluate/run_concurrent.py \\
    --method mot_plus \\
    --backend openai \\
    --model gpt-4o-mini \\
    --api-key YOUR_KEY \\
    --base-url https://aigc.sankuai.com/v1/openai/native \\
    --dataset humaneval \\
    --workers 8 \\
    --output results/humaneval_motplus_gpt4omini.jsonl

Then evaluate:
    python -m evalplus.evaluate --dataset humaneval \\
        --samples results/humaneval_motplus_gpt4omini.jsonl
"""
from __future__ import annotations

import sys
import json
import time
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mot.llm import LLMClient
from mot.mot_engine import MoTEngine
from mot.mot_plus import MoTPlusEngine
from mot.mot_sc import MoTSCEngine
from mot.mot_sc_plus import MoTSCPlusEngine
from mot.baselines import ZeroShot, FewShot, CoT, SelfPlanning, SCoT, CodeCoT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("evaluate.concurrent")

METHOD_NAMES = [
    "mot_sc_plus", "mot_sc", "mot_plus", "mot",
    "zero_shot", "few_shot", "cot", "self_planning", "scot", "codecot",
]


def build_method(name: str, llm: LLMClient):
    if name == "mot_sc_plus":
        return MoTSCPlusEngine(llm, n_samples=3, max_repair_rounds=2, exec_timeout=20)
    if name == "mot_sc":
        return MoTSCEngine(llm, n_samples=3, exec_timeout=20)
    if name == "mot_plus":
        return MoTPlusEngine(llm, max_repair_rounds=2, n_tests=6, exec_timeout=20)
    if name == "mot":
        return MoTEngine(llm)
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
    raise ValueError(f"Unknown method: {name!r}")


def load_problems(dataset: str) -> dict:
    if "humaneval" in dataset:
        from evalplus.data import get_human_eval_plus
        return get_human_eval_plus()
    else:
        from evalplus.data import get_mbpp_plus
        return get_mbpp_plus()


def build_task_description(problem: dict, dataset: str) -> str:
    return problem.get("prompt", "").strip()


def format_solution(solution: str, problem: dict) -> str:
    prompt = problem.get("prompt", "")
    import_lines = [
        ln for ln in prompt.splitlines()
        if ln.strip().startswith(("import ", "from "))
    ]
    if import_lines:
        header = "\n".join(import_lines)
        if not any(ln.strip() in solution for ln in import_lines):
            return header + "\n\n" + solution.strip()
    return solution.strip()


def parse_args():
    p = argparse.ArgumentParser(
        description="Concurrent code-generation evaluation (MoT / MoT+)"
    )
    p.add_argument("--method", default="mot_plus", choices=METHOD_NAMES)
    p.add_argument("--backend", default="openai", choices=["openai", "anthropic"])
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--api-key", default=None)
    p.add_argument("--base-url", default=None)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--max-tokens", type=int, default=2048)
    p.add_argument(
        "--dataset", default="humaneval",
        choices=["humaneval", "humaneval_plus", "mbpp", "mbpp_plus"],
    )
    p.add_argument("--workers", type=int, default=8,
                   help="Number of concurrent LLM workers (default: 8)")
    p.add_argument("--start-idx", type=int, default=0)
    p.add_argument("--end-idx", type=int, default=None)
    p.add_argument(
        "--output", default="results/{dataset}_{method}_{model}.jsonl",
        help="Output JSONL path ({dataset}, {method}, {model} auto-filled)",
    )
    return p.parse_args()


def main():
    args = parse_args()
    model_slug = args.model.replace("/", "_").replace(":", "_")
    output_str = args.output.format(
        dataset=args.dataset, method=args.method, model=model_slug
    )
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
            logger.info("Resuming: %d existing samples", len(existing))

    # Load dataset
    problems = load_problems(args.dataset)
    task_ids = sorted(problems.keys())
    task_ids = task_ids[args.start_idx: args.end_idx]
    task_ids = [t for t in task_ids if t not in existing]
    logger.info(
        "Evaluating %d problems | method=%s | model=%s | workers=%d",
        len(task_ids), args.method, args.model, args.workers,
    )

    # All MoT variants return (code, mlr_graph) tuple
    is_mot_variant = args.method in ("mot", "mot_plus", "mot_sc", "mot_sc_plus")
    write_lock = Lock()
    results = {}
    n_done = 0
    n_fail = 0

    def worker(task_id: str) -> dict:
        """Evaluate a single problem. Each worker has its own LLM + engine."""
        # All MoT variants generate modular code with multiple helper functions;
        # use at least 4096 tokens to avoid truncating complex solutions.
        effective_max_tokens = max(args.max_tokens, 4096)
        llm = LLMClient(
            backend=args.backend,
            model=args.model,
            api_key=args.api_key,
            base_url=args.base_url,
            temperature=args.temperature,
            max_tokens=effective_max_tokens,
        )
        method = build_method(args.method, llm)
        problem = problems[task_id]
        entry_point = problem.get("entry_point", "")
        task_desc = build_task_description(problem, args.dataset)

        t0 = time.time()
        mlr_graph = ""
        try:
            if is_mot_variant:
                code, mlr_graph = method.generate(task_desc, entry_point)
            else:
                code = method.generate(task_desc, entry_point)
        except Exception as exc:
            logger.warning("FAILED %s: %s", task_id, exc)
            code = f"# Error: {exc}\ndef {entry_point}(*args, **kwargs):\n    pass"

        elapsed = time.time() - t0
        solution = format_solution(code, problem)
        return {
            "task_id": task_id,
            "solution": solution,
            "mlr_graph": mlr_graph,
            "elapsed_sec": round(elapsed, 2),
        }

    t_start = time.time()
    with open(output_path, "a") as fout:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(worker, tid): tid for tid in task_ids}
            for future in as_completed(futures):
                tid = futures[future]
                try:
                    sample = future.result()
                    n_done += 1
                except Exception as exc:
                    logger.error("Worker exception for %s: %s", tid, exc)
                    n_fail += 1
                    continue

                with write_lock:
                    fout.write(json.dumps(sample, ensure_ascii=False) + "\n")
                    fout.flush()

                elapsed_total = time.time() - t_start
                rate = n_done / elapsed_total if elapsed_total > 0 else 0
                eta = (len(task_ids) - n_done) / rate if rate > 0 else 0
                logger.info(
                    "[%d/%d] %s  %.1fs  (rate=%.2f/s  ETA=%.0fs)",
                    n_done, len(task_ids), tid, sample["elapsed_sec"], rate, eta,
                )

    wall_time = time.time() - t_start
    logger.info("=" * 60)
    logger.info("Done. %d succeeded, %d failed. Wall time: %.0fs", n_done, n_fail, wall_time)
    logger.info("Output: %s", output_path)
    logger.info("")
    dataset_name = "humaneval" if "humaneval" in args.dataset else "mbpp"
    logger.info("Compute Pass@1:")
    logger.info("  python -m evalplus.evaluate --dataset %s --samples %s", dataset_name, output_path)


if __name__ == "__main__":
    main()
