"""
Baseline Scheduler - uses only mobility score for task assignment.
No trust or reliability considerations.
"""

from typing import List, Dict
from src.fog_node import FogNode
from src.task import Task
from src.dag_manager import DAGManager


class BaselineScheduler:
    """Baseline scheduler that uses only mobility score."""
    
    def __init__(self, nodes: List[FogNode], dag_manager: DAGManager):
        """
        Initialize baseline scheduler.
        
        Args:
            nodes: List of available fog nodes
            dag_manager: DAG manager for task dependencies
        """
        self.nodes = nodes
        self.dag_manager = dag_manager
        self.schedule: Dict[int, int] = {}  # task_id -> node_id mapping
    
    def schedule_tasks(self) -> Dict[int, int]:
        """
        Schedule all tasks based on mobility score only.
        
        Baseline scheduler is STATIC:
        - Uses only mobility score (no trust, no reliability)
        - No trust updates
        - No reliability updates
        - Fixed schedule (no dynamic reassignment)
        - Naturally performs worse because it doesn't learn from history
        
        Returns:
            Dictionary mapping task_id to node_id
        """
        self.schedule = {}
        topological_order = self.dag_manager.get_topological_order()
        
        # Sort nodes by mobility score (descending) - static ordering
        sorted_nodes = sorted(self.nodes, key=lambda n: n.get_mobility_score(), reverse=True)
        
        for task_id in topological_order:
            task = self.dag_manager.get_task(task_id)
            if task:
                # Baseline: always picks node with highest mobility score
                # This is static - doesn't consider trust or reliability
                best_node = sorted_nodes[0]  # Always the same node (highest mobility)
                
                self.schedule[task_id] = best_node.node_id
                task.assigned_node = best_node.node_id
        
        return self.schedule
    
    def get_schedule(self) -> Dict[int, int]:
        """Get the current schedule."""
        return self.schedule

