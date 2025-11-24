"""
DMITS scheduler using MRP-based mobility prediction and social trust.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .fog_node import FogNode
from .task import Task


@dataclass
class DMITSWeights:
    mobility: float = 0.5
    social: float = 0.45
    centrality: float = 0.05


class DMITSScheduler:
    """Implements the DMITS utility scoring without adaptive trust updates."""

    def __init__(self, nodes: List[FogNode], weights: DMITSWeights | None = None):
        self.nodes = nodes
        self.weights = weights or DMITSWeights()
        self.node_map: Dict[int, FogNode] = {node.node_id: node for node in nodes}

    def _score(self, node: FogNode, dependency_bonus: float) -> float:
        mobility_pred = node.compute_mobility_score()
        score = (
            self.weights.mobility * mobility_pred
            + self.weights.social * node.social_trust
            + self.weights.centrality * node.centrality
        )
        return score * dependency_bonus

    def select_node(self, task: Task) -> FogNode:
        """Select the highest-scoring node for the provided task."""
        dependency_bonus = 1.0 + 0.05 * len(task.dependencies)
        return max(self.nodes, key=lambda node: self._score(node, dependency_bonus))

    def on_task_result(self, node_id: int, success: bool) -> None:
        """DMITS does not update trust dynamically; method included for interface parity."""
        return


