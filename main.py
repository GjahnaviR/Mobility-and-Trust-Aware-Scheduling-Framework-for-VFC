"""
Main entry point for Vehicular Fog Network Scheduling Simulation.
Compares baseline (mobility-only) vs proposed (mobility + trust + reliability) schedulers.
"""

import csv
import os
from src.fog_node import FogNode
from src.task import Task
from src.simulator import Simulator
from src.metrics import Metrics
from src.plotter import Plotter
from src.mobility_processor import MobilityProcessor


def load_fog_nodes_from_csv(csv_file: str = "vehicular_data.csv", 
                           use_mobility_processor: bool = False) -> list:
    """
    Load fog nodes from CSV dataset.
    
    Supports two formats:
    1. Simple format: node_id,speed,success,failure
    2. Mobility format: vehicle_id,timestamp,distance,duration,speed (Porto-style)
    
    Args:
        csv_file: Path to CSV file
        use_mobility_processor: If True, use MobilityProcessor for trajectory data
        
    Returns:
        List of FogNode objects
    """
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        raise FileNotFoundError(f"{csv_file} not found")
    
    # Try to detect format by reading first line
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            headers = first_line.split(',')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        raise
    
    # Check if it's a mobility dataset (has trajectory columns)
    mobility_columns = ['vehicle_id', 'distance', 'duration', 'timestamp', 'latitude', 'longitude']
    is_mobility_format = any(col in headers for col in mobility_columns) or use_mobility_processor
    
    if is_mobility_format:
        # Use mobility processor for trajectory data
        print(f"Detected mobility/trajectory dataset format")
        try:
            nodes = MobilityProcessor.process_mobility_dataset(
                csv_file,
                vehicle_id_col='vehicle_id' if 'vehicle_id' in headers else headers[0],
                speed_col='speed' if 'speed' in headers else None,
                distance_col='distance' if 'distance' in headers else None,
                duration_col='duration' if 'duration' in headers else None
            )
            return nodes
        except Exception as e:
            print(f"Error processing mobility dataset: {e}")
            print("Falling back to simple format...")
            # Fall through to simple format
    
    # Simple format: node_id,speed,success,failure
    nodes = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                node_id = int(row['node_id'])
                speed = float(row['speed'])
                success = int(row['success'])
                failure = int(row['failure'])
                
                node = FogNode(
                    node_id=node_id,
                    speed=speed,
                    success=success,
                    failure=failure
                )
                nodes.append(node)
        print(f"✓ Loaded {len(nodes)} nodes from {csv_file} (simple format)")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        raise
    
    return nodes


def create_tasks(num_tasks: int = 8) -> list:
    """
    Create tasks with dependencies forming a DAG.
    
    Args:
        num_tasks: Number of tasks to create
        
    Returns:
        List of Task objects
    """
    tasks = []
    
    # Example DAG structure:
    # Task 1 -> Task 2, Task 3
    # Task 2 -> Task 4
    # Task 3 -> Task 4, Task 5
    # Task 4 -> Task 6
    # Task 5 -> Task 7
    # Task 6, Task 7 -> Task 8
    
    # Define task dependencies
    dependencies_map = {
        1: [],  # No dependencies
        2: [1],
        3: [1],
        4: [2, 3],
        5: [3],
        6: [4],
        7: [5],
        8: [6, 7]
    }
    
    # Execution times (in seconds) - deterministic
    execution_times = [2.0, 3.0, 2.5, 4.0, 3.5, 2.0, 2.5, 3.0]
    
    for i in range(1, min(num_tasks + 1, 9)):
        task_id = i
        deps = dependencies_map.get(i, [])
        exec_time = execution_times[i - 1] if i <= len(execution_times) else 3.0
        
        task = Task(
            task_id=task_id,
            execution_time=exec_time,
            dependencies=deps
        )
        tasks.append(task)
    
    # If more tasks needed, create additional independent tasks
    if num_tasks > 8:
        for i in range(9, num_tasks + 1):
            task = Task(
                task_id=i,
                execution_time=3.0,  # Fixed execution time for determinism
                dependencies=[]
            )
            tasks.append(task)
    
    return tasks


def main():
    """Main simulation function."""
    print("=" * 70)
    print("  Mobility and Trust-Aware Scheduling Framework")
    print("  for Vehicular Fog Networks - Dataset-Based Simulation")
    print("=" * 70)
    print()
    
    # Step 1: Load fog nodes from dataset
    print("Step 1: Loading fog nodes from dataset...")
    
    # Try to load from different dataset formats
    dataset_files = [
        "porto_mobility_sample.csv",  # Porto-style mobility dataset
        "vehicular_data.csv"           # Simple format
    ]
    
    nodes = None
    for dataset_file in dataset_files:
        if os.path.exists(dataset_file):
            try:
                nodes = load_fog_nodes_from_csv(dataset_file)
                print(f"✓ Loaded {len(nodes)} fog nodes from dataset")
                for node in nodes:
                    print(f"  {node}")
                print()
                break
            except Exception as e:
                print(f"Warning: Could not load {dataset_file}: {e}")
                continue
    
    if nodes is None or len(nodes) == 0:
        print("No dataset found. Creating sample dataset...")
        # Create sample Porto-format dataset
        sample_file = MobilityProcessor.create_sample_porto_format_dataset()
        nodes = load_fog_nodes_from_csv(sample_file)
        print(f"✓ Loaded {len(nodes)} fog nodes from sample dataset")
        for node in nodes:
            print(f"  {node}")
        print()
    
    # Step 2: Create tasks
    print("Step 2: Creating tasks with dependencies...")
    tasks = create_tasks(num_tasks=50)  # Increased to 50 tasks to show learning effect
    print(f"✓ Created {len(tasks)} tasks")
    for task in tasks:
        print(f"  {task}")
    print()
    
    # Step 3: Create simulator
    print("Step 3: Initializing simulator...")
    simulator = Simulator(nodes, tasks, seed=42)  # Deterministic seed
    print("✓ Simulator ready (deterministic mode)")
    print()
    
    # Step 4: Run baseline scheduling
    print("Step 4: Running baseline scheduler (mobility-only)...")
    # Reset nodes to initial state
    for node in nodes:
        node.reset_to_initial()
    baseline_time, baseline_completed, baseline_total = simulator.simulate_baseline()
    baseline_success_rate, baseline_avg_delay = Metrics.calculate_metrics(
        baseline_time, baseline_completed, baseline_total
    )
    print(f"✓ Baseline simulation completed")
    print(f"  Completed: {baseline_completed}/{baseline_total} tasks")
    print(f"  Total time: {baseline_time:.2f}s")
    print()
    
    # Step 5: Run proposed scheduling
    print("Step 5: Running proposed scheduler (mobility + trust + reliability)...")
    # Reset nodes to initial state for fair comparison
    for node in nodes:
        node.reset_to_initial()
    proposed_time, proposed_completed, proposed_total = simulator.simulate_proposed()
    proposed_success_rate, proposed_avg_delay = Metrics.calculate_metrics(
        proposed_time, proposed_completed, proposed_total
    )
    print(f"✓ Proposed simulation completed")
    print(f"  Completed: {proposed_completed}/{proposed_total} tasks")
    print(f"  Total time: {proposed_time:.2f}s")
    print()
    
    # Step 6: Print comparison results
    print("=" * 70)
    print("  COMPARISON RESULTS")
    print("=" * 70)
    print(f"Baseline Success Rate:  {baseline_success_rate:.1f}%")
    print(f"Proposed Success Rate:  {proposed_success_rate:.1f}%")
    print()
    print(f"Baseline Average Delay: {baseline_avg_delay:.2f}s")
    print(f"Proposed Average Delay: {proposed_avg_delay:.2f}s")
    print()
    
    # Calculate improvements
    success_improvement = proposed_success_rate - baseline_success_rate
    delay_improvement = baseline_avg_delay - proposed_avg_delay
    delay_improvement_pct = (delay_improvement / baseline_avg_delay * 100) if baseline_avg_delay > 0 else 0
    
    print("Improvements:")
    print(f"  Success Rate: +{success_improvement:.1f}% ({'↑' if success_improvement > 0 else '↓'})")
    print(f"  Average Delay: -{delay_improvement:.2f}s ({delay_improvement_pct:.1f}% {'↓' if delay_improvement > 0 else '↑'})")
    print()
    
    # Step 7: Generate plots
    print("Step 7: Generating comparison charts...")
    Plotter.plot_comparison(
        baseline_success_rate,
        proposed_success_rate,
        baseline_avg_delay,
        proposed_avg_delay
    )
    print()
    
    print("=" * 70)
    print("  Simulation completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()

