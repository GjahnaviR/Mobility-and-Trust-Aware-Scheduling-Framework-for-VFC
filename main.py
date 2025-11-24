"""
Run multi-trial comparison between DMITS and the proposed scheduler.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

from src.dataset_loader import load_nodes
from src.metrics import aggregate_stats, paired_t_test, rows_to_csv, summarize
from src.plotter import plot_with_error_bars
from src.scheduler_dmits import DMITSScheduler
from src.scheduler_proposed import ProposedConfig, ProposedScheduler
from src.simulator import FailureSettings, Simulator
from src.task import Task


def build_tasks(num_tasks: int, base_time: float = 2.5) -> List[Task]:
    tasks: List[Task] = []
    for task_id in range(1, num_tasks + 1):
        deps: List[int] = []
        if task_id > 3:
            deps.append(task_id - 3)
        if task_id > 5 and task_id % 5 == 0:
            deps.append(task_id - 5)
        execution_time = base_time + (task_id % 7) * 0.2
        tasks.append(Task(task_id=task_id, execution_time=execution_time, deps=deps, max_retries=3))
    return tasks


def clone_tasks(tasks: List[Task]) -> List[Task]:
    cloned: List[Task] = []
    for task in tasks:
        cloned.append(
            Task(
                task_id=task.task_id,
                execution_time=task.execution_time,
                deps=list(task.dependencies),
                max_retries=task.max_retries,
            )
        )
    return cloned


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DMITS vs Proposed scheduler comparison")
    parser.add_argument("--dataset", type=str, default="porto_mobility_sample.csv")
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--tasks", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--slope", type=float, default=4.0)
    parser.add_argument("--midpoint", type=float, default=0.3)
    parser.add_argument("--trust-weight", type=float, default=0.5)
    parser.add_argument("--mobility-weight", type=float, default=0.5)
    parser.add_argument("--results-dir", type=str, default="results")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    nodes = load_nodes(args.dataset)
    tasks_template = build_tasks(args.tasks)
    failure_settings = FailureSettings(slope=args.slope, midpoint=args.midpoint)
    simulator = Simulator(failure_settings=failure_settings)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    trial_rows: List[Dict] = []
    dmits_success: List[float] = []
    proposed_success: List[float] = []
    dmits_delay: List[float] = []
    proposed_delay: List[float] = []

    print(f"Loaded {len(nodes)} nodes from {args.dataset}")
    print(f"Running {args.trials} trials with {args.tasks} tasks each...\n")

    for trial in range(args.trials):
        trial_seed = args.seed + trial * 17
        nodes_dmits = [node.clone() for node in nodes]
        nodes_prop = [node.clone() for node in nodes]
        tasks_dmits = clone_tasks(tasks_template)
        tasks_prop = clone_tasks(tasks_template)

        dmits_sched = DMITSScheduler(nodes_dmits)
        proposed_sched = ProposedScheduler(
            nodes_prop,
            ProposedConfig(trust_weight=args.trust_weight, mobility_weight=args.mobility_weight),
        )

        dmits_result = simulator.run("DMITS", dmits_sched, nodes_dmits, tasks_dmits, trial_seed)
        proposed_result = simulator.run("PROPOSED", proposed_sched, nodes_prop, tasks_prop, trial_seed + 999)

        dmits_summary = summarize(dmits_result) | {"trial": trial}
        proposed_summary = summarize(proposed_result) | {"trial": trial}
        trial_rows.extend([dmits_summary, proposed_summary])

        dmits_success.append(dmits_summary["success_rate"])
        proposed_success.append(proposed_summary["success_rate"])
        dmits_delay.append(dmits_summary["avg_delay"])
        proposed_delay.append(proposed_summary["avg_delay"])

        print(
            f"Trial {trial:02d} | DMITS success {dmits_summary['success_rate']:.2f}% "
            f"delay {dmits_summary['avg_delay']:.3f}s | "
            f"PROPOSED success {proposed_summary['success_rate']:.2f}% "
            f"delay {proposed_summary['avg_delay']:.3f}s"
        )

    rows_to_csv(trial_rows, results_dir / "trial_results.csv")

    dmits_mean, dmits_std = aggregate_stats(dmits_success)
    proposed_mean, proposed_std = aggregate_stats(proposed_success)
    dmits_delay_mean, dmits_delay_std = aggregate_stats(dmits_delay)
    proposed_delay_mean, proposed_delay_std = aggregate_stats(proposed_delay)
    p_value = paired_t_test(proposed_success, dmits_success)

    stats_payload = [
        {
            "scheduler": "DMITS",
            "success_mean": dmits_mean,
            "success_std": dmits_std,
            "delay_mean": dmits_delay_mean,
            "delay_std": dmits_delay_std,
        },
        {
            "scheduler": "PROPOSED",
            "success_mean": proposed_mean,
            "success_std": proposed_std,
            "delay_mean": proposed_delay_mean,
            "delay_std": proposed_delay_std,
        },
    ]
    plot_with_error_bars(stats_payload, results_dir / "comparison_results.png")

    print("\nFinal Comparison (mean +/- std)")
    print(
        f"    DMITS | Success: {dmits_mean:.2f}% +/- {dmits_std:.2f} "
        f"| Avg Delay: {dmits_delay_mean:.3f}s +/- {dmits_delay_std:.3f}"
    )
    print(
        f" PROPOSED | Success: {proposed_mean:.2f}% +/- {proposed_std:.2f} "
        f"| Avg Delay: {proposed_delay_mean:.3f}s +/- {proposed_delay_std:.3f}"
    )
    print(f"\nPaired t-test p-value (success rate): {p_value:.4f}")

    avg_completed_dmits = int(round((dmits_mean / 100.0) * args.tasks))
    avg_completed_proposed = int(round((proposed_mean / 100.0) * args.tasks))
    print("\nRequired Summary Format")
    print(
        f"    DMITS | Success: {dmits_mean:.1f}% | Avg Delay: {dmits_delay_mean:.3f}s "
        f"| Completed: {avg_completed_dmits}/{args.tasks}"
    )
    print(
        f" PROPOSED | Success: {proposed_mean:.1f}% | Avg Delay: {proposed_delay_mean:.3f}s "
        f"| Completed: {avg_completed_proposed}/{args.tasks}"
    )

    summary_txt = results_dir / "summary.txt"
    with summary_txt.open("w", encoding="utf-8") as handle:
        handle.write("Multi-trial comparison between DMITS and Proposed scheduler\n")
        handle.write(f"Dataset: {args.dataset}\nTrials: {args.trials}\nTasks per trial: {args.tasks}\n")
        handle.write(f"Failure slope: {args.slope}, midpoint: {args.midpoint}\n\n")
        for entry in stats_payload:
            handle.write(
                f"{entry['scheduler']}: success {entry['success_mean']:.2f}% ± {entry['success_std']:.2f}, "
                f"avg delay {entry['delay_mean']:.3f}s ± {entry['delay_std']:.3f}\n"
            )
        handle.write(f"\nPaired t-test p-value (success): {p_value:.4f}\n")


if __name__ == "__main__":
    main()


