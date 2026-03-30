"""Parse Harbor job results into metrics for recursive-improve.

Copy this to eval/compute_baselines.py in your terminal-bench project.
Called automatically by `recursive-improve ratchet eval` when present.
"""

import argparse
import json
from pathlib import Path


def find_latest_job(jobs_dir: Path) -> Path | None:
    """Find the most recently modified job directory."""
    if not jobs_dir.exists():
        return None
    job_dirs = [d for d in jobs_dir.iterdir() if d.is_dir()]
    if not job_dirs:
        return None
    return max(job_dirs, key=lambda d: d.stat().st_mtime)


def parse_job_results(job_dir: Path) -> dict:
    """Parse a Harbor job directory into recursive-improve metrics."""
    passed = 0
    total = 0
    total_tokens = 0

    for trial_dir in sorted(job_dir.iterdir()):
        if not trial_dir.is_dir():
            continue

        result_path = trial_dir / "result.json"
        if not result_path.exists():
            continue

        result = json.loads(result_path.read_text())

        # Reward is at verifier_result.rewards.reward
        verifier = result.get("verifier_result") or {}
        rewards = verifier.get("rewards") or {}
        reward = rewards.get("reward", 0)

        total += 1
        if reward and reward > 0:
            passed += 1

        # Token counts from agent_result
        agent = result.get("agent_result") or {}
        total_tokens += agent.get("n_input_tokens", 0) + agent.get("n_output_tokens", 0)

    if total == 0:
        return {"metrics": {}}

    avg_tokens = total_tokens / total

    return {
        "metrics": {
            "resolution_rate": {
                "value": round(passed / total, 4),
                "numerator": passed,
                "denominator": total,
                "confidence": "full" if total >= 10 else "directional-only",
            },
            "avg_tokens": {
                "value": round(avg_tokens, 0),
                "numerator": total_tokens,
                "denominator": total,
                "confidence": "full",
            },
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--traces-dir", default="eval/traces")
    parser.add_argument("--output", default="eval/custom_metrics.json")
    parser.add_argument("--jobs-dir", default="jobs")
    args = parser.parse_args()

    job_dir = find_latest_job(Path(args.jobs_dir))
    if not job_dir:
        print(f"No job directory found in {args.jobs_dir}")
        result = {"metrics": {}}
    else:
        result = parse_job_results(job_dir)
        print(f"Job: {job_dir.name}")
        for name, m in result["metrics"].items():
            print(f"  {name}: {m['value']} ({m['numerator']}/{m['denominator']})")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
