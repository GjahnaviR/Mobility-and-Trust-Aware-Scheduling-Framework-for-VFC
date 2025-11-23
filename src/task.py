"""
Task model for vehicular fog computing simulation.
Each task has execution time, dependencies, and status tracking.
"""

from enum import Enum


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    """Represents a computational task with dependencies."""
    
    def __init__(self, task_id: int, execution_time: float, dependencies: list = None):
        """
        Initialize a task.
        
        Args:
            task_id: Unique identifier for the task
            execution_time: Time required to execute the task (in seconds)
            dependencies: List of task_ids that must complete before this task can run
        """
        self.task_id = task_id
        self.execution_time = execution_time
        self.dependencies = dependencies if dependencies is not None else []
        self.status = TaskStatus.PENDING
        self.assigned_node = None
        self.start_time = None
        self.completion_time = None
    
    def is_ready(self, completed_tasks: set) -> bool:
        """
        Check if all dependencies are completed.
        
        Args:
            completed_tasks: Set of task_ids that have been completed
            
        Returns:
            True if all dependencies are completed, False otherwise
        """
        return all(dep_id in completed_tasks for dep_id in self.dependencies)
    
    def assign_to_node(self, node_id: int):
        """Assign this task to a fog node."""
        self.assigned_node = node_id
        self.status = TaskStatus.RUNNING
    
    def mark_completed(self, completion_time: float):
        """Mark the task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completion_time = completion_time
    
    def mark_failed(self):
        """Mark the task as failed."""
        self.status = TaskStatus.FAILED
    
    def reset(self):
        """Reset task to initial state."""
        self.status = TaskStatus.PENDING
        self.assigned_node = None
        self.start_time = None
        self.completion_time = None
    
    def __repr__(self):
        deps_str = f", deps={self.dependencies}" if self.dependencies else ""
        return (f"Task(id={self.task_id}, time={self.execution_time:.2f}s, "
                f"status={self.status.value}{deps_str})")

