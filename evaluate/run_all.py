"""
Orchestrator: run all methods × all datasets to reproduce Table 1 of the paper.

Usage
-----
# Reproduce all GPT-4o-mini results (Table 1, top half):
python evaluate/run_all.py \\
    --backend openai \\
    --model gpt-4o-mini \\
    --methods mot cot scot zero_shot few_shot self_planning codecot \\
    --datasets humaneval humaneval_plus mbpp mbpp_plus \\
    --output-dir results/

# Reproduce MoT only:
python evaluate/run_all.py --methods mot --model gpt-4o-mini

# Dry-run (print commands without executing):
python evaluate/run_all.py --dry-run
"""
from __future__ import annotations

import sys
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ALL_METHODS = ["mot_plus", "mot", "zero_shot", "few_shot", "cot", "self_planning", "scot", "codecot"]
ALL_DATASETS = ["humaneval", "humaneval_plus", "mbpp", "mbpp_plus"]

HUMANEVAL_DATASETS = {"humaneval", "humaneval_plus"}
MBPP_DATASETS = {"mbpp", "mbpp_plus"}


def parse_args():
    p = argparse.ArgumentParser(
        description="Run all method × dataset combinations (MoT paper Table 1 reproduction)"
    )
    p.add_argument("--methods", nargs="+", default=ALL_METHODS, choices=ALL_METHODS)
    p.add_argument("--datasets", nargs="+", default=ALL_DATASETS, choices=ALL_DATASETS)
    p.add_argument("--backend", default="openai", choices=["openai", "anthropic"])
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--api-key", default=None)
    p.add_argument("--base-url", default=None)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--max-tokens", type=int, default=2048)
    p.add_argument("--output-dir", default="results")
    p.add_argument("--dry-run", action="store_true",
                   help="Print commands without executing them")
    return p.parse_args()


def build_command(
    method: str,
    dataset: str,
    backend: str,
    model: str,
    api_key: str | None,
    base_url: str | None,
    temperature: float,
    max_tokens: int,
    output_dir: str,
) -> list[str]:
    """Build the subprocess command for a single method × dataset run."""
    model_slug = model.replace("/", "_").replace(":", "_")

    if dataset in HUMANEVAL_DATASETS:
        script = "evaluate/run_humaneval.py"
        ds_arg = "humaneval" if dataset == "humaneval" else "humaneval_plus"
        ds_short = dataset.replace("_plus", "+")
    else:
        script = "evaluate/run_mbpp.py"
        ds_arg = "mbpp" if dataset == "mbpp" else "mbpp_plus"
        ds_short = dataset.replace("_plus", "+")

    output_file = str(
        Path(output_dir) / f"{dataset}_{method}_{model_slug}.jsonl"
    )

    cmd = [
        sys.executable, script,
        "--method", method,
        "--backend", backend,
        "--model", model,
        "--dataset", ds_arg,
        "--temperature", str(temperature),
        "--max-tokens", str(max_tokens),
        "--output", output_file,
    ]
    if api_key:
        cmd += ["--api-key", api_key]
    if base_url:
        cmd += ["--base-url", base_url]
    return cmd


def main():
    args = parse_args()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    total = len(args.methods) * len(args.datasets)
    print(f"\nMoT Paper Reproduction — {total} runs planned")
    print(f"  Backend : {args.backend}  Model : {args.model}")
    print(f"  Methods : {args.methods}")
    print(f"  Datasets: {args.datasets}")
    print(f"  Output  : {args.output_dir}/\n")

    n = 0
    for method in args.methods:
        for dataset in args.datasets:
            n += 1
            cmd = build_command(
                method=method,
                dataset=dataset,
                backend=args.backend,
                model=args.model,
                api_key=args.api_key,
                base_url=args.base_url,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                output_dir=args.output_dir,
            )
            print(f"[{n}/{total}] {method} × {dataset}")
            print("  " + " ".join(cmd))

            if args.dry_run:
                print("  [DRY RUN — skipped]")
            else:
                result = subprocess.run(cmd, check=False)
                if result.returncode != 0:
                    print(f"  WARNING: command returned exit code {result.returncode}")
            print()

    if not args.dry_run:
        print("All runs complete.")
        print("\nTo compute Pass@1 for all datasets, run:")
        for dataset in args.datasets:
            evalplus_ds = "humaneval" if "humaneval" in dataset else "mbpp"
            model_slug = args.model.replace("/", "_").replace(":", "_")
            for method in args.methods:
                fp = Path(args.output_dir) / f"{dataset}_{method}_{model_slug}.jsonl"
                print(
                    f"  python -m evalplus.evaluate --dataset {evalplus_ds} "
                    f"--samples {fp}"
                )


if __name__ == "__main__":
    main()
