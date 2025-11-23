# Mobility and Trust-Aware Scheduling Framework for Vehicular Fog Networks

A **dataset-based** simulation project that compares two scheduling methods in vehicular fog computing:

1. **Baseline Scheduler** - Uses only mobility to assign tasks
2. **Proposed Scheduler** - Uses mobility + trust + reliability with dynamic task rearrangement

## Project Structure

```
.
├── src/
│   ├── fog_node.py          # Fog node class with mobility, trust, reliability
│   ├── task.py              # Task model with dependencies
│   ├── dag_manager.py       # DAG manager for topological sorting
│   ├── scheduler_baseline.py # Baseline scheduler (mobility-only)
│   ├── scheduler_proposed.py # Proposed scheduler (mobility + trust + reliability)
│   ├── simulator.py         # Task execution simulator
│   ├── metrics.py           # Performance metrics calculation
│   ├── plotter.py           # Visualization with matplotlib
│   └── mobility_processor.py # Real mobility dataset processor
├── vehicular_data.csv       # Simple format dataset
├── porto_mobility_sample.csv # Porto-format mobility dataset (auto-generated)
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── DATASET_GUIDE.md         # Guide for using real mobility datasets
```

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the simulation:
```bash
python main.py
```

The program will:
1. Load fog nodes from `vehicular_data.csv` dataset
2. Create tasks with dependencies (DAG structure)
3. Run baseline scheduling simulation
4. Run proposed scheduling simulation
5. Calculate and display metrics
6. Generate comparison bar charts

## Dataset Formats

The project supports **two dataset formats**:

### 1. Simple Format (Default)
File: `vehicular_data.csv`
```csv
node_id,speed,success,failure
1,40,20,3
2,70,14,5
```

### 2. Real Mobility Dataset Format (Porto/TAPAS Style)
File: `porto_mobility_sample.csv` or any trajectory dataset
```csv
vehicle_id,timestamp,latitude,longitude,distance,duration,speed
1,1000,41.15,-8.61,2.5,0.05,50.0
```

**The system automatically detects the format and processes it accordingly.**

For detailed instructions on using real mobility datasets (Porto Taxi, TAPASCologne, Beijing Taxi), see **[DATASET_GUIDE.md](DATASET_GUIDE.md)**.

## Key Features

### Fog Node Metrics (from Dataset)

- **Mobility Score**: `mobility = 1 / speed` (lower speed = higher mobility)
- **Trust Score**: `trust = success / (success + failure)` (calculated from dataset)
- **Reliability Score**: `reliability = 0.6 * trust + 0.4 * mobility_score`
- **Trust Updates** (during execution):
  - +0.02 on successful task execution
  - -0.05 on failed task execution
  - Clamped between 0 and 1

### Scheduling Algorithms

**Baseline**: 
- Assigns tasks to nodes with highest mobility score only
- Tasks fail if `speed > 90`

**Proposed**: 
- Assigns tasks to nodes with highest reliability score
- Rearranges tasks dynamically based on reliability
- Recalculates reliability after each task
- Updates trust after each execution
- Tasks fail if `speed > 90 OR random failure < 5%`

**Proposed**: 
- Computes reliability scores (trust + mobility)
- Rearranges tasks dynamically based on reliability
- Updates trust after each execution
- Recomputes reliability after every task

### Performance Metrics

- **Success Rate**: `(completed_tasks / total_tasks) * 100`
- **Average Delay**: `total_execution_time / total_tasks`

## Output

The simulation outputs:
- Console comparison of success rates and delays
- Two bar charts comparing baseline vs proposed schedulers
- Saved plot as `comparison_results.png`

## Example Output

```
Baseline Success Rate:  70.0%
Proposed Success Rate:  88.0%

Baseline Average Delay: 12.50s
Proposed Average Delay: 8.10s
```

