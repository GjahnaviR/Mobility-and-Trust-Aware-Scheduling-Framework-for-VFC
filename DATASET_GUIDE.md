# Real Mobility Datasets Guide

This guide explains how to use real vehicular mobility datasets with this project.

## Supported Dataset Formats

### 1. Simple Format (Current Default)
File: `vehicular_data.csv`
```csv
node_id,speed,success,failure
1,40,20,3
2,70,14,5
```

### 2. Porto Taxi Format (Recommended for Real Data)
File: `porto_mobility_sample.csv` or your Porto dataset
```csv
vehicle_id,timestamp,latitude,longitude,distance,duration,speed
1,1000,41.15,-8.61,2.5,0.05,50.0
1,1060,41.16,-8.62,2.8,0.05,56.0
```

## Using Real Datasets

### Option 1: Porto Taxi Dataset (Kaggle)

1. **Download the dataset:**
   - Visit: https://www.kaggle.com/datasets/henriqueyamahata/porto-taxi-trajectories-dataset
   - Download the CSV file

2. **Place it in the project directory:**
   ```bash
   # Rename to porto_mobility_sample.csv or keep original name
   cp your_downloaded_file.csv porto_mobility_sample.csv
   ```

3. **Run the simulation:**
   ```bash
   python main.py
   ```
   The system will automatically detect and process the Porto format.

### Option 2: TAPASCologne Dataset

1. **Download from SUMO:**
   - Visit: https://sumo.dlr.de/docs/Data/Scenarios/TAPASCologne.html
   - Extract vehicle trajectory data

2. **Convert to CSV format:**
   - Ensure columns: `vehicle_id`, `timestamp`, `speed` (or `distance` + `duration`)
   - Save as CSV

3. **Use with the project:**
   ```python
   from src.mobility_processor import MobilityProcessor
   nodes = MobilityProcessor.process_mobility_dataset("your_tapas_file.csv")
   ```

### Option 3: Beijing Taxi Dataset

1. **Download from Microsoft Research:**
   - Visit: https://www.microsoft.com/en-us/research/publication/t-drive-trajectory-data-sample/
   - Extract GPS trajectory data

2. **Process the data:**
   ```python
   import pandas as pd
   from src.mobility_processor import MobilityProcessor
   
   # Load and preprocess
   df = pd.read_csv("beijing_taxi.csv")
   # Ensure columns: vehicle_id, timestamp, latitude, longitude
   # Add distance and duration if not present
   
   nodes = MobilityProcessor.process_mobility_dataset("beijing_taxi.csv")
   ```

## Creating Sample Datasets

If you don't have a real dataset, the system can generate a sample:

```python
from src.mobility_processor import MobilityProcessor

# Create sample Porto-format dataset
MobilityProcessor.create_sample_porto_format_dataset(
    output_file="my_sample.csv",
    num_vehicles=10,
    records_per_vehicle=100
)
```

## Dataset Column Requirements

### Minimum Required Columns:
- **Simple format:** `node_id`, `speed`, `success`, `failure`
- **Mobility format:** `vehicle_id` (or first column), `speed` OR (`distance` + `duration`)

### Optional Columns (for enhanced processing):
- `timestamp` - For temporal analysis
- `latitude`, `longitude` - For spatial analysis
- `distance` - Distance traveled
- `duration` - Time duration

## How Trust is Computed from Mobility

The system automatically computes trust from mobility patterns:

1. **Speed Consistency:** Lower variance in speed = higher trust
2. **Speed Range:** Moderate speeds (30-90 km/h) = higher trust
3. **High-Speed Ratio:** More time above 90 km/h = lower trust

Formula:
```python
trust = 0.6 * consistency_score + 0.4 * speed_range_score
```

## Example: Processing Your Own Dataset

```python
import pandas as pd
from src.mobility_processor import MobilityProcessor

# Load your dataset
df = pd.read_csv("your_data.csv")

# Ensure it has required columns
# If not, add them:
if 'speed' not in df.columns and 'distance' in df.columns and 'duration' in df.columns:
    df['speed'] = df['distance'] / df['duration']

# Process and create fog nodes
nodes = MobilityProcessor.process_mobility_dataset("your_data.csv")

# Use in simulation
from src.simulator import Simulator
from src.task import Task

tasks = [...]  # Your tasks
simulator = Simulator(nodes, tasks)
results = simulator.simulate_proposed()
```

## Dataset Sources

1. **Porto Taxi Dataset (Recommended):**
   - https://www.kaggle.com/datasets/henriqueyamahata/porto-taxi-trajectories-dataset
   - Clean, well-formatted, easy to use

2. **TAPASCologne:**
   - https://sumo.dlr.de/docs/Data/Scenarios/TAPASCologne.html
   - Large-scale urban traffic simulation

3. **Beijing Taxi:**
   - https://www.microsoft.com/en-us/research/publication/t-drive-trajectory-data-sample/
   - Real GPS trajectory data

4. **CRAWDAD:**
   - https://crawdad.org
   - Multiple vehicular mobility datasets

## Troubleshooting

**Problem:** "Error: CSV file not found"
- **Solution:** Ensure the CSV file is in the project root directory

**Problem:** "Need either 'speed' column or 'distance' and 'duration' columns"
- **Solution:** Add a `speed` column or ensure `distance` and `duration` columns exist

**Problem:** "No vehicle_id column found"
- **Solution:** Rename your vehicle identifier column to `vehicle_id` or use the first column

**Problem:** Dataset too large
- **Solution:** Sample the dataset or use `pandas` to filter:
  ```python
  df = pd.read_csv("large_file.csv")
  df_sample = df.sample(n=10000)  # Sample 10k records
  df_sample.to_csv("sample.csv", index=False)
  ```


