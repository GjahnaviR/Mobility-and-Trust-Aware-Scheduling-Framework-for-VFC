"""
Baseline schedulers: FCFS and SJF.

These are simple, traditional strategies used only in the
`extra_plots.py` helper script to generate additional comparison
figures (FCFS, SJF, DMITS, Proposed).  They do NOT affect the main
`main.py` experiment pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .fog_node import FogNode
from .task import Task


@dataclass
class FCFSScheduler:
    """First-Come-First-Served style baseline.

    The DAG manager already decides which tasks are ready and in what
    order they are considered.  This scheduler simply assigns each task
    to fog nodes in a round-robin fashion, ignoring trust and mobility.
    """

    nodes: List[FogNode]

    def __post_init__(self) -> None:
        self._index = 0

    def select_node(self, task: Task) -> FogNode:  # noqa: ARG002
        node = self.nodes[self._index]
        self._index = (self._index + 1) % len(self.nodes)
        return node

    def on_task_result(self, node_id: int, success: bool) -> None:  # noqa: ARG002
        # FCFS does not adapt based on outcomes.
        return


@dataclass
class SJFScheduler:
    """Shortest-Job-First style baseline.

    The DAG manager still determines which tasks are ready at a given
    time, but this scheduler prefers assigning shorter tasks to nodes
    with higher reliability.
    """

    nodes: List[FogNode]

    def __post_init__(self) -> None:
        self.node_map: Dict[int, FogNode] = {node.node_id: node for node in self.nodes}

    def _score(self, node: FogNode, task: Task) -> float:
        # Prefer highly reliable nodes for short tasks; for longer tasks
        # the score flattens towards the base reliability.
        length_factor = 1.0 / max(task.execution_time, 0.1)
        return node.reliability_score * length_factor

    def select_node(self, task: Task) -> FogNode:
        return max(self.nodes, key=lambda n: self._score(n, task))

    def on_task_result(self, node_id: int, success: bool) -> None:  # noqa: ARG002
        # SJF baseline does not update trust / reliability dynamically.
        return


