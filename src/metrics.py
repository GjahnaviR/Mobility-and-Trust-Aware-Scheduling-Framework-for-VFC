"""
Metrics calculation module for performance evaluation.
"""

from typing import Tuple


class Metrics:
    """Calculate performance metrics for scheduling algorithms."""
    
    @staticmethod
    def calculate_success_rate(completed_tasks: int, total_tasks: int) -> float:
        """
        Calculate task success rate.
        
        Args:
            completed_tasks: Number of successfully completed tasks
            total_tasks: Total number of tasks
            
        Returns:
            Success rate as percentage (0-100)
        """
        if total_tasks == 0:
            return 0.0
        return (completed_tasks / total_tasks) * 100.0
    
    @staticmethod
    def calculate_average_delay(total_execution_time: float, completed_tasks: int) -> float:
        """
        Calculate average delay per completed task.
        
        Args:
            total_execution_time: Total time taken to execute tasks
            completed_tasks: Number of successfully completed tasks
            
        Returns:
            Average delay per completed task in seconds
        """
        if completed_tasks == 0:
            return 0.0
        return total_execution_time / completed_tasks
    
    @staticmethod
    def calculate_metrics(total_execution_time: float, completed_tasks: int, 
                         total_tasks: int) -> Tuple[float, float]:
        """
        Calculate both success rate and average delay.
        
        Args:
            total_execution_time: Total execution time
            completed_tasks: Number of completed tasks
            total_tasks: Total number of tasks
            
        Returns:
            Tuple of (success_rate, average_delay)
        """
        success_rate = Metrics.calculate_success_rate(completed_tasks, total_tasks)
        avg_delay = Metrics.calculate_average_delay(total_execution_time, completed_tasks)
        return success_rate, avg_delay

