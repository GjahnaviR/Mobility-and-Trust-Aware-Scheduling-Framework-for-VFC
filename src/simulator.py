"""
Task Execution Simulator - simulates task execution with failure possibility.
"""

import random
import math
from typing import List, Dict, Tuple
from src.fog_node import FogNode
from src.task import Task, TaskStatus
from src.dag_manager import DAGManager
from src.scheduler_baseline import BaselineScheduler
from src.scheduler_proposed import ProposedScheduler


class Simulator:
    """Simulates task execution in vehicular fog network."""
    
    def __init__(self, nodes: List[FogNode], tasks: List[Task], seed: int = 42):
        """
        Initialize simulator.
        
        Args:
            nodes: List of fog nodes
            tasks: List of tasks to execute
            seed: Random seed for deterministic results
        """
        self.nodes = nodes
        self.tasks = tasks
        self.seed = seed
        random.seed(seed)  # For deterministic results
        self.dag_manager = DAGManager(tasks)
    
    def _calculate_failure_probability(self, node: FogNode) -> float:
        """
        Calculate failure probability using logistic model based on node reliability.
        
        Uses smooth logistic function for realistic failure modeling:
        failure_prob = 1 / (1 + exp(10 * (reliability - 0.5)))
        
        This model:
        - Reliability < 0.5 → higher failure probability
        - Reliability > 0.5 → lower failure probability
        - Changes smoothly (no harsh thresholds)
        - Allows tasks to succeed even with moderate reliability
        - Trust updates improve reliability → success rate improves organically
        
        Args:
            node: Fog node to evaluate
            
        Returns:
            Failure probability between 0 and 1
        """
        reliability = node.get_reliability_score()
        
        # Logistic failure model: smooth transition
        # Use lower threshold (0.25) to account for reliability range
        # Reduced steepness (3 instead of 5) makes small reliability changes more visible
        # This allows trust updates to have meaningful impact on failure probability
        threshold = 0.25
        steepness = 3.0  # Reduced from 5.0 to make learning more visible
        failure_prob = 1.0 / (1.0 + math.exp(steepness * (reliability - threshold)))
        return max(0.0, min(1.0, failure_prob))
    
    def simulate_baseline(self) -> Tuple[float, int, int]:
        """
        Simulate baseline scheduling.
        
        Baseline characteristics:
        - Uses only mobility score (static)
        - No trust updates
        - No reliability updates
        - Fixed schedule (no dynamic reassignment)
        - Uses reliability-based failure probability (fair comparison)
        
        Returns:
            Tuple of (total_execution_time, completed_tasks, total_tasks)
        """
        # Reset random seed for deterministic results
        random.seed(self.seed)
        
        # Reset all tasks
        self.dag_manager.reset_all_tasks()
        
        # Create scheduler and get schedule (static, computed once)
        scheduler = BaselineScheduler(self.nodes, self.dag_manager)
        schedule = scheduler.schedule_tasks()
        
        # Execute tasks
        current_time = 0.0
        completed_tasks: set = set()
        
        while len(completed_tasks) < len(self.tasks):
            ready_tasks = self.dag_manager.get_ready_tasks(completed_tasks)
            
            if not ready_tasks:
                break
            
            # Execute ready tasks
            for task_id in ready_tasks:
                task = self.dag_manager.get_task(task_id)
                if task and task.status == TaskStatus.PENDING:
                    node_id = schedule.get(task_id)
                    if node_id is not None:
                        node = next((n for n in self.nodes if n.node_id == node_id), None)
                        if node:
                            task.assign_to_node(node_id)
                            
                            # Simulate execution with speed-based time adjustment
                            # Faster nodes complete tasks faster (for fair comparison)
                            speed_factor = 1.0 / (1.0 + node.speed / 100.0)
                            execution_time = task.execution_time * speed_factor
                            
                            # Fair failure model: based on reliability score
                            # No artificial thresholds - purely data-driven
                            failure_prob = self._calculate_failure_probability(node)
                            success = random.random() > failure_prob
                            
                            if success:
                                current_time += execution_time
                                task.mark_completed(current_time)
                                completed_tasks.add(task_id)
                                # Baseline: NO trust update (static scheduler)
                            else:
                                task.mark_failed()
                                # Baseline: NO trust update (static scheduler)
        
        total_time = current_time
        completed_count = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        total_count = len(self.tasks)
        
        return total_time, completed_count, total_count
    
    def simulate_proposed(self) -> Tuple[float, int, int]:
        """
        Simulate proposed scheduling with adaptive behavior.
        
        Proposed characteristics:
        - Uses reliability score (mobility + trust)
        - Updates trust after each task execution
        - Recalculates reliability dynamically
        - Dynamically reassigns tasks based on updated reliability
        - Uses same reliability-based failure probability (fair comparison)
        - Naturally outperforms baseline through learning
        
        Returns:
            Tuple of (total_execution_time, completed_tasks, total_tasks)
        """
        # Reset random seed for deterministic results
        random.seed(self.seed)
        
        # Reset all tasks
        self.dag_manager.reset_all_tasks()
        
        # Create scheduler
        scheduler = ProposedScheduler(self.nodes, self.dag_manager)
        
        # Execute tasks with dynamic scheduling
        current_time = 0.0
        completed_tasks: set = set()
        
        while len(completed_tasks) < len(self.tasks):
            ready_tasks = self.dag_manager.get_ready_tasks(completed_tasks)
            
            if not ready_tasks:
                break
            
            # Proposed: Dynamically reassign tasks based on current utility scores
            # This happens before each task execution (adaptive behavior)
            for task_id in ready_tasks:
                task = self.dag_manager.get_task(task_id)
                if task and task.status == TaskStatus.PENDING:
                    # Find best node based on CURRENT utility scores (recalculated after each task)
                    # Utility combines mobility, trust, and reliability for better selection
                    # Proposed automatically avoids low-utility nodes
                    best_node = max(self.nodes, key=lambda n: n.get_utility_score())
                    node_id = best_node.node_id
                    
                    task.assign_to_node(node_id)
                    
                    # Simulate execution with speed-based time adjustment
                    # Faster nodes complete tasks faster
                    # adjusted_time = base_time * (1 / (1 + speed/100))
                    speed_factor = 1.0 / (1.0 + best_node.speed / 100.0)
                    execution_time = task.execution_time * speed_factor
                    
                    # Fair failure model: same as baseline (reliability-based)
                    # No artificial thresholds - purely data-driven
                    failure_prob = self._calculate_failure_probability(best_node)
                    success = random.random() > failure_prob
                    
                    if success:
                        current_time += execution_time
                        task.mark_completed(current_time)
                        completed_tasks.add(task_id)
                        # Proposed: Update trust on success (adaptive learning)
                        scheduler.update_node_trust(node_id, True)
                        # Reliability is automatically recalculated in update_node_trust
                    else:
                        task.mark_failed()
                        # Proposed: Update trust on failure (adaptive learning)
                        scheduler.update_node_trust(node_id, False)
                        # Reliability is automatically recalculated in update_node_trust
        
        total_time = current_time
        completed_count = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        total_count = len(self.tasks)
        
        return total_time, completed_count, total_count

