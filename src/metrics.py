"""
Metrics helpers for experiment reporting.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy import stats


def success_rate(completed: int, total: int) -> float:
    return (completed / total) * 100.0 if total else 0.0


def average_delay(total_time: float, completed: int) -> float:
    return total_time / completed if completed else float("nan")


def summarize(result: Dict) -> Dict:
    completed = result["completed_tasks"]
    total = result["total_tasks"]
    total_time = result["total_time"]

    # QoS-style metrics derived from simulation output
    makespan = total_time  # overall completion time for all finished tasks
    throughput = completed / total_time if total_time > 0 else 0.0  # tasks per second

    # Approximate per-task latency as the same as average delay in this
    # simple single-server time model; in more complex models, latency
    # would usually be measured per task using start/finish timestamps.
    avg_delay_val = average_delay(total_time, completed)
    latency = avg_delay_val

    # Simple energy model: assume a fixed dynamic energy cost per task
    # execution attempt plus a small idle cost proportional to makespan.
    # This is synthetic but allows relative comparison between schedulers.
    per_task_energy = 1.0
    idle_power = 0.05
    num_attempts = completed + len(result.get("failed_tasks", []))
    energy = per_task_energy * num_attempts + idle_power * makespan

    return {
        "scheduler": result["scheduler"],
        "success_rate": success_rate(completed, total),
        "avg_delay": avg_delay_val,
        "makespan": makespan,
        "throughput": throughput,
        "latency": latency,
        "energy": energy,
        "completed_tasks": completed,
        "total_tasks": total,
        "total_time": total_time,
        "seed": result["seed"],
    }


def aggregate_stats(values: Sequence[float]) -> Tuple[float, float]:
    arr = np.array(values, dtype=float)
    if len(arr) <= 1:
        return float(arr.mean()) if len(arr) else 0.0, 0.0
    return float(arr.mean()), float(np.std(arr, ddof=1))


def paired_t_test(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or not x:
        return float("nan")
    stat = stats.ttest_rel(x, y, nan_policy="omit")
    return float(stat.pvalue)


def rows_to_csv(rows: List[Dict], path: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


