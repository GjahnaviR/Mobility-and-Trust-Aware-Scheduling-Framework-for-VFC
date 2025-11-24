"""
Adaptive scheduler combining mobility, trust, and reliability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .fog_node import FogNode
from .task import Task


@dataclass
class ProposedConfig:
    trust_weight: float = 0.5
    mobility_weight: float = 0.5
    trust_inc: float = 0.05
    trust_dec: float = 0.10


class ProposedScheduler:
    """Dynamic scheduler with trust updates and task rearrangement."""

    def __init__(self, nodes: List[FogNode], config: ProposedConfig | None = None):
        self.nodes = nodes
        self.config = config or ProposedConfig()
        self.node_map: Dict[int, FogNode] = {node.node_id: node for node in nodes}

    def _score(self, node: FogNode) -> float:
        node.compute_mobility_score()
        node.compute_reliability(trust_weight=self.config.trust_weight, mobility_weight=self.config.mobility_weight)
        return node.reliability_score

    def select_node(self, task: Task) -> FogNode:
        """Recompute ranking before each assignment (dynamic rearrangement)."""
        return max(self.nodes, key=self._score)

    def on_task_result(self, node_id: int, success: bool) -> None:
        node = self.node_map[node_id]
        node.update_trust(success, inc=self.config.trust_inc, dec=self.config.trust_dec)


