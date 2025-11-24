# A Mobility and Trust-Aware Scheduling Framework for Vehicular Fog Networks

This repository implements a reproducible, dataset-driven simulator that compares two schedulers for vehicular fog computing:

1. **DMITS** baseline – Markov Renewal Process (MRP) mobility prediction + social trust + dependency-aware static scheduling.
2. **Proposed AMTS-VFC** scheduler – mobility + trust + reliability fusion with dynamic rearrangement and online trust adaptation.

Both schedulers share the same dataset, DAG workload, and logistic failure model to ensure a fair comparison. Multi-trial experiments (default 30 runs) quantify performance gaps with mean ± std metrics and paired t-tests.

---

## 1. Requirements & Setup

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt  # numpy, pandas, matplotlib, scikit-learn, scipy, pytest
```

---

## 2. Dataset Processing Pipeline

### Supported Input
- Porto taxi sample (`porto_mobility_sample.csv`) or any CSV containing:
  ```
  node_id (or vehicle_id), speed, success_count, fail_count, [optional route/time columns]
  ```
- If `node_id` is absent, `vehicle_id` is renamed automatically.
- Missing success/failure counts are synthesized via speed variance heuristics.

### Steps (see `src/dataset_loader.py`)
1. **Group by node** to collect speed traces.
2. **MRP Mobility** (`src/mobility_predictor.py`):
   - Discretize speed into `SLOW (<40)`, `MEDIUM (40-80)`, `FAST (>80)`.
   - Build transition matrix `P(s_{t+1} | s_t)` by counting transitions and normalizing rows.
   - Mobility score = stay probability in reachable regions:
     ```
     mobility = P(SLOW | current_state) + P(MEDIUM | current_state)
     ```
3. **Trust & Social Trust**:
   ```
   trust = success_count / (success_count + fail_count)   # or synthesized fallback
   social_trust = trust                                    # used by DMITS when explicit data absent
   ```
4. **Reliability**:
   ```
   reliability = 0.5 * trust + 0.5 * mobility
   ```
5. **Centrality proxy**: `1 - mean(normalized_speed)` (slower nodes assumed more stable).
6. Instantiate `FogNode` objects with transition models, trust, mobility, reliability, social trust, and centrality. Nodes expose:
   - `compute_mobility_score()` – updates mobility via the MRP stay probability.
   - `compute_reliability(trust_weight, mobility_weight)`.
   - `update_trust(success, inc=0.05, dec=0.10)` – used by the adaptive scheduler.
   - `clone()` and `reset()` – ensure each scheduler run has isolated state.

---

## 3. Task Model & DAG Manager
- `src/task.py`: tasks carry execution time, dependency list, retry count (default max 3 attempts).
- `src/dag_manager.py` provides `get_ready_tasks`, `get_topological_order`, and cycle detection.
- Default workload: 50 tasks with realistic dependencies (each task depends on the one three positions earlier; every fifth task links to task_id-5).

---

## 4. Scheduler Algorithms

### DMITS (`src/scheduler_dmits.py`)
```
mobility_pred = node.compute_mobility_score()
U = 0.5 * mobility_pred + 0.45 * social_trust + 0.05 * centrality
U *= (1 + 0.05 * len(task.dependencies))        # dependency-aware boost
```
- Picks node with max `U`.
- Trust remains static (no updates after task execution).

### Proposed AMTS-VFC (`src/scheduler_proposed.py`)
```
reliability = trust_weight * trust + mobility_weight * mobility   # default weights = 0.5 / 0.5
```
- Recomputes reliability for all nodes before each assignment (dynamic rearrangement).
- After execution:
  ```
  trust += 0.05 if success else -0.10
  reliability recomputed immediately (clamped trust in [0,1])
  ```
- Failing nodes quickly drop in reliability, steering future tasks toward more stable vehicles.

---

## 5. Failure Model & Simulator (`src/simulator.py`)

### Logistic Failure Probability (shared)
```
p_fail = 1 / (1 + exp(slope * (reliability - midpoint)))
```
- Defaults: `slope = 4.0`, `midpoint = 0.3`.
- Both schedulers use identical parameters and RNG seeds.

### Execution Flow
1. Build DAG and maintain completed/failed sets.
2. Iterate while ready tasks exist:
   - Scheduler selects node.
   - Draw success/failure using logistic probability and deterministic RNG seeded per trial.
   - On success: mark completed, accumulate execution time.
   - On failure: increment retry counter (max 2 retries). If retries remain, re-queue task; otherwise mark failed.
   - Notify scheduler (`on_task_result`) so Proposed can update trust.
3. Log per-node success/failure counts and timestamps for reproducibility.

---

## 6. Experiment Driver (`main.py`)

### CLI Arguments
```
--dataset           CSV path (default: porto_mobility_sample.csv)
--trials            Number of trials (default: 30)
--tasks             Tasks per trial (default: 50)
--seed              Base RNG seed
--slope, --midpoint Logistic failure parameters
--trust-weight, --mobility-weight  Reliability weights for Proposed scheduler
--results-dir       Output directory (default: results)
```

### Workflow
1. Load nodes, build task template.
2. For each trial `t`:
   - Seeds: `seed + 17*t` (DMITS), `seed + 17*t + 999` (Proposed).
   - Clone nodes/tasks for both schedulers.
   - Run simulator for DMITS and Proposed; summarize success rate and average delay:
     ```
     success_rate = completed / total * 100
     avg_delay    = total_time / completed
     ```
3. Aggregate across trials:
   - Compute mean ± std for each scheduler.
   - Perform paired t-test (`scipy.stats.ttest_rel`) on success-rate vectors.
4. Outputs (under `results/`):
   - `trial_results.csv` – per-trial metrics.
   - `comparison_results.png` – success/delay bar charts with error bars.
   - `summary.txt` – narrative summary with p-values and parameter settings.

### Console Sample (10 trials, 50 tasks, seed 42)
```
Final Comparison (mean +/- std)
    DMITS | Success: 92.40% +/- 24.03 | Avg Delay: 3.411s +/- 0.207
 PROPOSED | Success: 100.00% +/- 0.00 | Avg Delay: 3.315s +/- 0.124

Required Summary Format
    DMITS | Success: 92.4% | Avg Delay: 3.411s | Completed: 46/50
 PROPOSED | Success: 100.0% | Avg Delay: 3.315s | Completed: 50/50
```
(Default configuration with 30 trials yields tighter confidence intervals.)

---

## 7. Component Map

```
src/
  dataset_loader.py      # CSV ingestion + FogNode creation
  mobility_predictor.py  # MRP utilities (state discretization, transitions)
  trust_manager.py       # Clamped trust update helper
  fog_node.py            # Vehicle state (trust, mobility, reliability)
  dag_manager.py         # DAG ready-task and topo logic
  task.py                # Task model with retry support
  scheduler_dmits.py     # DMITS scoring (mobility + social + centrality)
  scheduler_proposed.py  # Reliability-based adaptive scheduler
  simulator.py           # Logistic failure engine shared by both schedulers
  metrics.py             # Success/delay metrics, aggregate stats, paired t-test, CSV writer
  plotter.py             # Error-bar charts (mean ± std)
tests/test_core.py       # Unit tests (reliability bounds, DAG readiness, failure monotonicity)
main.py                  # Multi-trial CLI orchestrator
results/                 # Generated CSV/PNG/TXT artifacts
```

---

## 8. Metrics & Statistical Analysis
- **Success Rate**: `(completed_tasks / total_tasks) * 100`.
- **Average Delay**: `total_time / completed_tasks`.
- **Aggregation**: mean ± std across all trials (unbiased sample std).
- **Paired t-test**: `scipy.stats.ttest_rel` on success-rate vectors of Proposed vs DMITS to gauge significance.
- **Visualization**: error-bar plots for both metrics (mean ± std).

---

## 9. Testing

```bash
python -m pytest
```

`tests/test_core.py` covers:
1. Reliability stays within [0, 1].
2. DAG manager enforces dependency ordering.
3. Failure probability decreases as reliability increases (logistic model sanity check).

---

## 10. Findings & Comparison

| Feature                     | DMITS Baseline                                  | Proposed AMTS-VFC                                    |
|-----------------------------|--------------------------------------------------|------------------------------------------------------|
| Mobility predictor          | MRP stay probability                             | Same                                                 |
| Trust behavior              | Static (no updates)                              | Online updates (+0.05 / -0.10) per execution         |
| Task allocation             | Single assignment based on initial utility       | Tasks reassigned dynamically using latest reliability |
| Failure adaptation          | Retries without trust adjustment                 | Retries with trust decay ⇒ unreliable nodes avoided  |
| Expected performance        | Moderate (sensitive to initial estimates)        | Higher success rate and lower delay over time        |

Sample run (10 trials) showed Proposed completing every task with lower mean delay, while DMITS occasionally suffered large drops (e.g., Trial 0) when early failures were not corrected by trust updates.

---

## 11. Extending the Framework
- Swap in larger datasets or real traces by changing `--dataset`.
- Tune failure parameters (`--slope`, `--midpoint`) or scheduler weights via CLI.
- Implement additional schedulers by adhering to the `select_node` / `on_task_result` interface.
- Replace the social-trust proxy with real co-location metrics if available.

---

## 12. Quick Start Recap

```bash
pip install -r requirements.txt
python main.py --dataset porto_mobility_sample.csv --trials 30 --tasks 50 --seed 42
python -m pytest
```

Artifacts (CSV, PNG, TXT) will appear in `results/`, and the console prints detailed and spec-required comparisons. This provides a complete, reproducible assessment of DMITS vs the proposed mobility + trust-aware scheduler.***

