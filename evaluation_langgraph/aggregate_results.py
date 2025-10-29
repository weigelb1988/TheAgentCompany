#!/usr/bin/env python3
"""
Result aggregation and analysis for LangGraph agent evaluation.

This script analyzes evaluation results from all tasks and generates summary statistics.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any


def load_results(output_dir: Path) -> List[Dict[str, Any]]:
    """Load all evaluation results from output directory."""
    results = []

    for eval_file in sorted(output_dir.glob("eval_*.json")):
        try:
            with open(eval_file) as f:
                data = json.load(f)

            task_name = eval_file.stem.replace("eval_", "")
            final_score = data.get("final_score", {})

            # Extract category from task name (e.g., "sde-find-bug" -> "sde")
            category = task_name.split("-")[0] if "-" in task_name else "other"

            results.append(
                {
                    "task": task_name,
                    "category": category,
                    "score": final_score.get("result", 0),
                    "total": final_score.get("total", 0),
                    "percentage": (final_score.get("result", 0) / final_score.get("total", 1) * 100)
                    if final_score.get("total", 0) > 0
                    else 0,
                    "checkpoints": data.get("checkpoints", []),
                }
            )
        except Exception as e:
            print(f"Warning: Could not load {eval_file}: {e}")

    return results


def load_trajectories(output_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Load trajectory information."""
    trajectories = {}

    for traj_file in sorted(output_dir.glob("traj_*.json")):
        try:
            with open(traj_file) as f:
                data = json.load(f)

            task_name = data.get("task_name", traj_file.stem.replace("traj_", ""))
            trajectories[task_name] = {
                "iterations": data.get("total_iterations", 0),
                "trajectory_steps": len(data.get("trajectory", [])),
                "completed_steps": len(data.get("completed_steps", [])),
                "execution_time": data.get("execution_time_seconds", 0),
            }
        except Exception as e:
            print(f"Warning: Could not load {traj_file}: {e}")

    return trajectories


def print_summary(results: List[Dict[str, Any]], trajectories: Dict[str, Dict[str, Any]]):
    """Print comprehensive summary of results."""

    if not results:
        print("No results found!")
        return

    # Overall statistics
    total_tasks = len(results)
    total_score = sum(r["score"] for r in results)
    total_possible = sum(r["total"] for r in results)
    average_percentage = sum(r["percentage"] for r in results) / total_tasks if total_tasks > 0 else 0

    perfect_scores = len([r for r in results if r["percentage"] == 100])
    partial_scores = len([r for r in results if 0 < r["percentage"] < 100])
    zero_scores = len([r for r in results if r["percentage"] == 0])

    print("=" * 70)
    print("OVERALL RESULTS")
    print("=" * 70)
    print(f"Total tasks:        {total_tasks}")
    print(f"Total score:        {total_score}/{total_possible} ({total_score/total_possible*100:.1f}%)")
    print(f"Average score:      {average_percentage:.2f}%")
    print(f"Perfect scores:     {perfect_scores} ({perfect_scores/total_tasks*100:.1f}%)")
    print(f"Partial scores:     {partial_scores} ({partial_scores/total_tasks*100:.1f}%)")
    print(f"Zero scores:        {zero_scores} ({zero_scores/total_tasks*100:.1f}%)")
    print()

    # Execution statistics
    if trajectories:
        avg_iterations = sum(t["iterations"] for t in trajectories.values()) / len(trajectories)
        avg_time = sum(t.get("execution_time", 0) for t in trajectories.values()) / len(trajectories)

        print("=" * 70)
        print("EXECUTION STATISTICS")
        print("=" * 70)
        print(f"Average iterations: {avg_iterations:.1f}")
        print(f"Average time:       {avg_time:.1f}s")
        print()

    # Category breakdown
    categories = defaultdict(list)
    for result in results:
        categories[result["category"]].append(result)

    print("=" * 70)
    print("CATEGORY BREAKDOWN")
    print("=" * 70)
    print(f"{'Category':<15} {'Count':<8} {'Avg Score':<12} {'Perfect':<10}")
    print("-" * 70)

    for category in sorted(categories.keys()):
        cat_results = categories[category]
        count = len(cat_results)
        avg_score = sum(r["percentage"] for r in cat_results) / count
        perfect = len([r for r in cat_results if r["percentage"] == 100])

        print(f"{category:<15} {count:<8} {avg_score:>6.1f}%      {perfect}/{count}")

    print()

    # Top 10 tasks
    print("=" * 70)
    print("TOP 10 TASKS")
    print("=" * 70)
    sorted_results = sorted(results, key=lambda x: x["percentage"], reverse=True)
    for i, result in enumerate(sorted_results[:10], 1):
        task = result["task"]
        score = result["score"]
        total = result["total"]
        pct = result["percentage"]
        print(f"{i:2}. {task:<40} {score}/{total} ({pct:.1f}%)")
    print()

    # Bottom 10 tasks
    print("=" * 70)
    print("BOTTOM 10 TASKS")
    print("=" * 70)
    for i, result in enumerate(sorted_results[-10:][::-1], 1):
        task = result["task"]
        score = result["score"]
        total = result["total"]
        pct = result["percentage"]
        print(f"{i:2}. {task:<40} {score}/{total} ({pct:.1f}%)")
    print()


def save_csv(results: List[Dict[str, Any]], trajectories: Dict[str, Dict[str, Any]], output_path: Path):
    """Save results to CSV file."""
    import csv

    csv_path = output_path / "results_summary.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "task",
                "category",
                "score",
                "total",
                "percentage",
                "iterations",
                "trajectory_steps",
                "execution_time",
            ]
        )

        # Data
        for result in sorted(results, key=lambda x: x["task"]):
            task_name = result["task"]
            traj = trajectories.get(task_name, {})

            writer.writerow(
                [
                    result["task"],
                    result["category"],
                    result["score"],
                    result["total"],
                    f"{result['percentage']:.1f}",
                    traj.get("iterations", ""),
                    traj.get("trajectory_steps", ""),
                    f"{traj.get('execution_time', 0):.1f}",
                ]
            )

    print(f"Results saved to: {csv_path}")


def save_json_summary(
    results: List[Dict[str, Any]], trajectories: Dict[str, Dict[str, Any]], output_path: Path
):
    """Save summary as JSON."""
    total_tasks = len(results)
    average_percentage = sum(r["percentage"] for r in results) / total_tasks if total_tasks > 0 else 0

    # Category statistics
    categories = defaultdict(list)
    for result in results:
        categories[result["category"]].append(result)

    category_stats = {}
    for category, cat_results in categories.items():
        category_stats[category] = {
            "count": len(cat_results),
            "average_percentage": sum(r["percentage"] for r in cat_results) / len(cat_results),
            "perfect_scores": len([r for r in cat_results if r["percentage"] == 100]),
        }

    summary = {
        "total_tasks": total_tasks,
        "average_percentage": average_percentage,
        "perfect_scores": len([r for r in results if r["percentage"] == 100]),
        "partial_scores": len([r for r in results if 0 < r["percentage"] < 100]),
        "zero_scores": len([r for r in results if r["percentage"] == 0]),
        "category_stats": category_stats,
        "tasks": results,
    }

    json_path = output_path / "results_summary.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"JSON summary saved to: {json_path}")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python aggregate_results.py <output_directory>")
        sys.exit(1)

    output_dir = Path(sys.argv[1])

    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}")
        sys.exit(1)

    print("Loading results...")
    results = load_results(output_dir)
    trajectories = load_trajectories(output_dir)

    if not results:
        print("No evaluation results found!")
        sys.exit(1)

    print(f"Loaded {len(results)} task results")
    print()

    # Print summary
    print_summary(results, trajectories)

    # Save outputs
    save_csv(results, trajectories, output_dir)
    save_json_summary(results, trajectories, output_dir)

    print()
    print("=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
