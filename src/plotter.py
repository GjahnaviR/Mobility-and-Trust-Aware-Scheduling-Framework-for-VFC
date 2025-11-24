"""
Plotting utilities for experiment summaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import matplotlib.pyplot as plt


def plot_with_error_bars(stats: List[dict], output_path: str) -> None:
    if not stats:
        return

    schedulers = [entry["scheduler"].upper() for entry in stats]
    indices = list(range(len(schedulers)))
    colors = ["#34495e", "#2ecc71"]

    success_means = [entry["success_mean"] for entry in stats]
    success_stds = [entry["success_std"] for entry in stats]
    delay_means = [entry["delay_mean"] for entry in stats]
    delay_stds = [entry["delay_std"] for entry in stats]

    fig, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

    # Success subplot
    bars_success = axes[0].bar(
        indices,
        success_means,
        yerr=success_stds,
        capsize=8,
        color=colors,
        alpha=0.85,
        edgecolor="black",
    )
    axes[0].set_ylabel("Success Rate (%)")
    axes[0].set_ylim(0, 105)
    axes[0].set_title("Success Rate (mean ± std)", fontsize=12, fontweight="bold")
    axes[0].grid(axis="y", linestyle="--", alpha=0.3)
    for bar, mean, std in zip(bars_success, success_means, success_stds):
        axes[0].text(
            bar.get_x() + bar.get_width() / 2,
            mean + std + 1,
            f"{mean:.1f}%\n±{std:.1f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    # Delay subplot
    bars_delay = axes[1].bar(
        indices,
        delay_means,
        yerr=delay_stds,
        capsize=8,
        color=colors,
        alpha=0.85,
        edgecolor="black",
    )
    axes[1].set_ylabel("Average Delay (seconds)")
    axes[1].set_title("Average Delay (mean ± std)", fontsize=12, fontweight="bold")
    axes[1].grid(axis="y", linestyle="--", alpha=0.3)
    axes[1].set_xticks(indices)
    axes[1].set_xticklabels(schedulers, fontsize=11, fontweight="bold")
    for bar, mean, std in zip(bars_delay, delay_means, delay_stds):
        axes[1].text(
            bar.get_x() + bar.get_width() / 2,
            mean + std + 0.02,
            f"{mean:.3f}s\n±{std:.3f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    fig.suptitle("Scheduler Comparison (DMITS vs Proposed)", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


