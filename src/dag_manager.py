"""
DAG Manager for handling task dependencies and topological sorting.
Ensures tasks are executed only after their dependencies are completed.
"""

from typing import List, Set
from src.task import Task, TaskStatus


class DAGManager:
    """Manages Directed Acyclic Graph of tasks with dependencies."""
    
    def __init__(self, tasks: List[Task]):
        """
        Initialize DAG manager with a list of tasks.
        
        Args:
            tasks: List of Task objects
        """
        self.tasks = {task.task_id: task for task in tasks}
        self.task_ids = list(self.tasks.keys())
    
    def get_topological_order(self) -> List[int]:
        """
        Get tasks in topological order (dependency order).
        
        Returns:
            List of task_ids in execution order
        """
        # Build adjacency list and in-degree count
        in_degree = {task_id: 0 for task_id in self.task_ids}
        graph = {task_id: [] for task_id in self.task_ids}
        
        for task in self.tasks.values():
            for dep_id in task.dependencies:
                if dep_id in self.tasks:
                    graph[dep_id].append(task.task_id)
                    in_degree[task.task_id] += 1
        
        # Kahn's algorithm for topological sort
        queue = [task_id for task_id in self.task_ids if in_degree[task_id] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def get_ready_tasks(self, completed_tasks: Set[int]) -> List[int]:
        """
        Get list of task IDs that are ready to execute (all dependencies completed).
        
        Args:
            completed_tasks: Set of completed task IDs
            
        Returns:
            List of ready task IDs
        """
        ready = []
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING and task.is_ready(completed_tasks):
                ready.append(task_id)
        return ready
    
    def get_task(self, task_id: int) -> Task:
        """Get a task by its ID."""
        return self.tasks.get(task_id)
    
    def reset_all_tasks(self):
        """Reset all tasks to initial state."""
        for task in self.tasks.values():
            task.reset()
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks as a list."""
        return list(self.tasks.values())
    
    def has_cycles(self) -> bool:
        """
        Check if the DAG has cycles (should not happen in valid DAG).
        
        Returns:
            True if cycles detected, False otherwise
        """
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            
            task = self.tasks[node_id]
            for dep_id in task.dependencies:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for task_id in self.task_ids:
            if task_id not in visited:
                if has_cycle(task_id):
                    return True
        
        return False

