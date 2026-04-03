"""
Generate additional comparison graphs for FCFS, SJF, DMITS, and Proposed.

This script does NOT change the main experiment pipeline in `main.py`.
It is an extra utility that sweeps over:

1. Number of tasks  -> service delay
2. Number of vehicles -> service delay
3. Vehicle speed scaling -> service delay

and writes three PNG figures into the `results/` directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt

from src.dataset_loader import load_nodes
from src.scheduler_baseline import FCFSScheduler, SJFScheduler
from src.scheduler_dmits import DMITSScheduler
from src.scheduler_proposed import ProposedConfig, ProposedScheduler
from src.simulator import FailureSettings, Simulator
from src.task import Task

from main import build_tasks, clone_tasks


RESULTS_DIR = Path("results")


def _run_single_setting(
    nodes_all,
    num_tasks: int,
    num_vehicles: int,
    speed_scale: float,
    trials: int,
    base_seed: int,
    failure_settings: FailureSettings,
) -> Dict[str, float]:
    """Run all four schedulers under a single configuration and
    return average service delay (avg_delay) per scheduler.
    """
    # Select subset of vehicles
    if num_vehicles > len(nodes_all):
        nodes_base = nodes_all
    else:
        nodes_base = nodes_all[:num_vehicles]

    # Apply speed scaling (conceptually varying vehicle speed)
    for node in nodes_base:
        node.speed *= speed_scale

    tasks_template: List[Task] = build_tasks(num_tasks)
    simulator = Simulator(failure_settings=failure_settings)

    delays: Dict[str, List[float]] = {"FCFS": [], "SJF": [], "DMITS": [], "PROPOSED": []}

    for trial in range(trials):
        seed = base_seed + trial * 17

        nodes_fcfs = [n.clone() for n in nodes_base]
        nodes_sjf = [n.clone() for n in nodes_base]
        nodes_dmits = [n.clone() for n in nodes_base]
        nodes_prop = [n.clone() for n in nodes_base]

        tasks_fcfs = clone_tasks(tasks_template)
        tasks_sjf = clone_tasks(tasks_template)
        tasks_dmits = clone_tasks(tasks_template)
        tasks_prop = clone_tasks(tasks_template)

        fcfs_sched = FCFSScheduler(nodes_fcfs)
        sjf_sched = SJFScheduler(nodes_sjf)
        dmits_sched = DMITSScheduler(nodes_dmits)
        proposed_sched = ProposedScheduler(nodes_prop, ProposedConfig())

        fcfs_res = simulator.run("FCFS", fcfs_sched, nodes_fcfs, tasks_fcfs, seed)
        sjf_res = simulator.run("SJF", sjf_sched, nodes_sjf, tasks_sjf, seed)
        dmits_res = simulator.run("DMITS", dmits_sched, nodes_dmits, tasks_dmits, seed)
        prop_res = simulator.run("PROPOSED", proposed_sched, nodes_prop, tasks_prop, seed)

        delays["FCFS"].append(fcfs_res["total_time"] / fcfs_res["completed_tasks"])
        delays["SJF"].append(sjf_res["total_time"] / sjf_res["completed_tasks"])
        delays["DMITS"].append(dmits_res["total_time"] / dmits_res["completed_tasks"])
        delays["PROPOSED"].append(prop_res["total_time"] / prop_res["completed_tasks"])

    # Return mean delay per scheduler
    return {name: sum(vals) / len(vals) for name, vals in delays.items()}


def _plot_service_delay(
    x_values: List[float],
    y_values: Dict[str, List[float]],
    x_label: str,
    output_name: str,
) -> None:
    plt.figure(figsize=(6, 4))
    markers = {"FCFS": "o", "SJF": "s", "DMITS": "D", "PROPOSED": "^"}
    # Use a very distinct colour and style for SJF so that it is
    # clearly visible even when curves overlap.
    colors = {"FCFS": "#34495e", "SJF": "#ff00ff", "DMITS": "#3498db", "PROPOSED": "#2ecc71"}

    for name in ["FCFS", "SJF", "DMITS", "PROPOSED"]:
        style = "-" if name != "SJF" else "--"
        linewidth = 1.5 if name != "SJF" else 2.2
        plt.plot(
            x_values,
            y_values[name],
            linestyle=style,
            linewidth=linewidth,
            marker=markers[name],
            markersize=6 if name != "SJF" else 8,
            markeredgecolor="black" if name == "SJF" else None,
            color=colors[name],
            label=name,
            zorder=3 if name == "SJF" else 2,
        )

    plt.xlabel(x_label)
    plt.ylabel("Service Delay (s)")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.legend()
    plt.tight_layout()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / output_name
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    # Base configuration consistent with your main experiments
    dataset = "porto_mobility_sample.csv"
    trials = 20
    base_seed = 42
    failure_settings = FailureSettings(slope=5.0, midpoint=0.35)

    nodes_all = load_nodes(dataset)

    print(f"Loaded {len(nodes_all)} nodes from {dataset}")
    print("Generating extra service-delay comparison plots (FCFS, SJF, DMITS, PROPOSED)...\n")

    # 1) Service delay vs number of tasks
    task_counts = [100, 200, 300, 400, 500]
    delays_vs_tasks: Dict[str, List[float]] = {k: [] for k in ["FCFS", "SJF", "DMITS", "PROPOSED"]}
    for num_tasks in task_counts:
        metrics = _run_single_setting(
            nodes_all=nodes_all,
            num_tasks=num_tasks,
            num_vehicles=min(30, len(nodes_all)),
            speed_scale=1.0,
            trials=trials,
            base_seed=base_seed,
            failure_settings=failure_settings,
        )
        for name in delays_vs_tasks:
            delays_vs_tasks[name].append(metrics[name])

    _plot_service_delay(
        x_values=task_counts,
        y_values=delays_vs_tasks,
        x_label="Number of Tasks",
        output_name="extra_service_delay_vs_tasks.png",
    )

    # 2) Service delay vs number of vehicles
    vehicle_counts = [10, 20, 30, 40, 50]
    delays_vs_vehicles: Dict[str, List[float]] = {k: [] for k in ["FCFS", "SJF", "DMITS", "PROPOSED"]}
    for num_vehicles in vehicle_counts:
        metrics = _run_single_setting(
            nodes_all=nodes_all,
            num_tasks=100,
            num_vehicles=min(num_vehicles, len(nodes_all)),
            speed_scale=1.0,
            trials=trials,
            base_seed=base_seed + 1000,
            failure_settings=failure_settings,
        )
        for name in delays_vs_vehicles:
            delays_vs_vehicles[name].append(metrics[name])

    _plot_service_delay(
        x_values=vehicle_counts,
        y_values=delays_vs_vehicles,
        x_label="Number of Vehicles",
        output_name="extra_service_delay_vs_vehicles.png",
    )

    # 3) Service delay vs vehicle speed (implemented as global speed scaling)
    speed_scales = [0.6, 0.8, 1.0, 1.2, 1.4]
    # Represent them as approximate speeds in km/h for the x-axis (relative)
    speed_labels = [int(50 * s) for s in speed_scales]
    delays_vs_speed: Dict[str, List[float]] = {k: [] for k in ["FCFS", "SJF", "DMITS", "PROPOSED"]}
    for scale in speed_scales:
        metrics = _run_single_setting(
            nodes_all=nodes_all,
            num_tasks=100,
            num_vehicles=min(30, len(nodes_all)),
            speed_scale=scale,
            trials=trials,
            base_seed=base_seed + 2000,
            failure_settings=failure_settings,
        )
        for name in delays_vs_speed:
            delays_vs_speed[name].append(metrics[name])

    _plot_service_delay(
        x_values=speed_labels,
        y_values=delays_vs_speed,
        x_label="Vehicle Speed (relative units)",
        output_name="extra_service_delay_vs_speed.png",
    )

    print("Extra plots written to `results/`:")
    print("  - extra_service_delay_vs_tasks.png")
    print("  - extra_service_delay_vs_vehicles.png")
    print("  - extra_service_delay_vs_speed.png")


if __name__ == "__main__":
    main()

