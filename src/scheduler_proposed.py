"""
Proposed Scheduler - uses mobility + trust + reliability with dynamic rearrangement.
"""

from typing import List, Dict, Set
from src.fog_node import FogNode
from src.task import Task
from src.dag_manager import DAGManager


class ProposedScheduler:
    """Proposed scheduler using mobility, trust, and reliability with task rearrangement."""
    
    def __init__(self, nodes: List[FogNode], dag_manager: DAGManager):
        """
        Initialize proposed scheduler.
        
        Args:
            nodes: List of available fog nodes
            dag_manager: DAG manager for task dependencies
        """
        self.nodes = nodes
        self.dag_manager = dag_manager
        self.schedule: Dict[int, int] = {}  # task_id -> node_id mapping
    
    def _rearrange_tasks_by_utility(self, ready_tasks: List[int]) -> List[int]:
        """
        Rearrange ready tasks based on node utility scores.
        Tasks are sorted to prioritize assignment to high-utility nodes.
        
        Utility combines mobility, trust, and reliability for better selection.
        
        Args:
            ready_tasks: List of ready task IDs
            
        Returns:
            Rearranged list of task IDs
        """
        # Get utility scores for all nodes
        node_utilities = {node.node_id: node.get_utility_score() 
                         for node in self.nodes}
        
        # Sort tasks by assigning them to nodes and sorting by node utility
        # This is a simplified rearrangement - in practice, you might want
        # a more sophisticated matching algorithm
        task_utility_pairs = []
        for task_id in ready_tasks:
            # Find best node for this task based on utility
            best_node = max(self.nodes, key=lambda n: n.get_utility_score())
            task_utility_pairs.append((task_id, best_node.get_utility_score()))
        
        # Sort by utility score (descending)
        task_utility_pairs.sort(key=lambda x: x[1], reverse=True)
        return [task_id for task_id, _ in task_utility_pairs]
    
    def schedule_tasks(self) -> Dict[int, int]:
        """
        Schedule all tasks based on reliability score with dynamic rearrangement.
        
        Returns:
            Dictionary mapping task_id to node_id
        """
        self.schedule = {}
        completed_tasks: Set[int] = set()
        
        # Process tasks in dependency order, but rearrange ready tasks by reliability
        while len(completed_tasks) < len(self.dag_manager.task_ids):
            # Get all ready tasks
            ready_tasks = self.dag_manager.get_ready_tasks(completed_tasks)
            
            if not ready_tasks:
                break
            
            # Rearrange ready tasks based on utility
            rearranged_tasks = self._rearrange_tasks_by_utility(ready_tasks)
            
            # Assign each ready task to the node with highest utility
            for task_id in rearranged_tasks:
                task = self.dag_manager.get_task(task_id)
                if task:
                    # Find node with highest utility score
                    best_node = max(self.nodes, key=lambda n: n.get_utility_score())
                    self.schedule[task_id] = best_node.node_id
                    task.assigned_node = best_node.node_id
                    completed_tasks.add(task_id)
        
        return self.schedule
    
    def update_node_trust(self, node_id: int, success: bool):
        """
        Update trust value of a node after task execution.
        +0.10 on success, -0.15 on failure
        
        Larger trust updates make reliability changes more visible and impactful.
        Combined with logistic failure model, this creates natural learning behavior.
        Reliability is automatically recalculated after each trust update.
        
        Args:
            node_id: ID of the node
            success: True if task succeeded, False if failed
        """
        node = next((n for n in self.nodes if n.node_id == node_id), None)
        if node:
            if success:
                node.update_trust_on_success()  # +0.10
            else:
                node.update_trust_on_failure()  # -0.15
            # Reliability is automatically recalculated in _update_scores()
    
    def get_schedule(self) -> Dict[int, int]:
        """Get the current schedule."""
        return self.schedule

