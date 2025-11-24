"""
Simulation utilities for executing tasks under different schedulers.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List

from .dag_manager import DAGManager
from .fog_node import FogNode
from .task import Task, TaskStatus


@dataclass
class FailureSettings:
    slope: float = 4.0
    midpoint: float = 0.3


class Simulator:
    """Runs a single scheduler on a set of nodes/tasks."""

    def __init__(self, failure_settings: FailureSettings | None = None, max_retries: int = 2):
        self.failure_settings = failure_settings or FailureSettings()
        self.max_retries = max_retries

    def _failure_probability(self, reliability: float) -> float:
        s = self.failure_settings.slope
        m = self.failure_settings.midpoint
        return 1.0 / (1.0 + math.exp(s * (reliability - m)))

    def run(
        self,
        scheduler_name: str,
        scheduler,
        nodes: List[FogNode],
        tasks: List[Task],
        seed: int,
    ) -> Dict:
        rng = random.Random(seed)
        dag = DAGManager(tasks)
        completed: set[int] = set()
        failed: set[int] = set()
        current_time = 0.0
        per_node_success = {node.node_id: 0 for node in nodes}
        per_node_failure = {node.node_id: 0 for node in nodes}
        logs: List[Dict] = []

        safety_counter = 0
        max_iters = len(tasks) * 10

        while len(completed) + len(failed) < len(tasks) and safety_counter < max_iters:
            safety_counter += 1
            ready_ids = dag.get_ready_tasks(completed)
            if not ready_ids:
                break

            for task_id in ready_ids:
                task = dag.get_task(task_id)
                if task.status != TaskStatus.PENDING:
                    continue

                node = scheduler.select_node(task)
                failure_prob = self._failure_probability(node.reliability_score)
                success = rng.random() >= failure_prob
                current_time += task.execution_time

                if success:
                    task.mark_completed(current_time)
                    completed.add(task.task_id)
                    per_node_success[node.node_id] += 1
                else:
                    task.mark_failed()
                    per_node_failure[node.node_id] += 1
                    task.increment_retry()
                    if task.retry_count <= self.max_retries:
                        task.status = TaskStatus.PENDING
                        task.assigned_node = None
                    else:
                        failed.add(task.task_id)

                scheduler.on_task_result(node.node_id, success)
                logs.append(
                    {
                        "task_id": task.task_id,
                        "node_id": node.node_id,
                        "success": success,
                        "time": current_time,
                        "reliability": node.reliability_score,
                    }
                )

            if safety_counter >= max_iters:
                break

        total_tasks = len(tasks)
        return {
            "scheduler": scheduler_name,
            "total_time": current_time,
            "completed_tasks": len(completed),
            "total_tasks": total_tasks,
            "failed_tasks": list(failed),
            "per_node_success": per_node_success,
            "per_node_failure": per_node_failure,
            "logs": logs,
            "seed": seed,
        }


