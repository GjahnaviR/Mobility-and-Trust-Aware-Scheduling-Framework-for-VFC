"""
Dataset loader that converts CSV records into FogNode objects.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from .fog_node import FogNode
from .mobility_predictor import TransitionModel, build_transition_model, discretize_speed, normalize_speed_features


def _ensure_id_column(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure there is a node_id column, falling back to vehicle_id when needed."""
    if "node_id" in df.columns:
        return df
    if "vehicle_id" in df.columns:
        df = df.rename(columns={"vehicle_id": "node_id"})
        return df
    raise ValueError("Dataset must contain either 'node_id' or 'vehicle_id'.")


def _extract_success_failure(df: pd.DataFrame) -> Tuple[str | None, str | None]:
    success_cols = [col for col in df.columns if col.lower() in {"success", "success_count", "past_success"}]
    failure_cols = [col for col in df.columns if col.lower() in {"failure", "fail_count", "past_failure"}]
    success_col = success_cols[0] if success_cols else None
    failure_col = failure_cols[0] if failure_cols else None
    return success_col, failure_col


def _synthetic_counts(speeds: List[float]) -> Tuple[int, int]:
    """Generate synthetic success/failure counts when columns are missing."""
    variance = np.var(speeds) if speeds else 0.0
    baseline = max(10, len(speeds))
    success_ratio = 0.8 - min(0.3, variance / 200.0)
    success = max(5, int(baseline * success_ratio))
    failure = max(1, baseline - success)
    return success, failure


def load_nodes(csv_path: str) -> List[FogNode]:
    """Load fog nodes from a CSV dataset."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = _ensure_id_column(pd.read_csv(path))
    if "speed" not in df.columns:
        raise ValueError("Dataset must contain a 'speed' column.")

    success_col, failure_col = _extract_success_failure(df)

    nodes: List[FogNode] = []
    for node_id, group in df.groupby("node_id"):
        speeds = group["speed"].astype(float).tolist()
        transition_model = build_transition_model(speeds)
        current_state = discretize_speed(speeds[-1])
        avg_speed = float(np.mean(speeds))
        speed_features = normalize_speed_features(speeds)
        centrality = 1.0 - float(np.mean(speed_features))

        if success_col and failure_col:
            success_count = int(group[success_col].iloc[0])
            failure_count = int(group[failure_col].iloc[0])
        else:
            success_count, failure_count = _synthetic_counts(speeds)
        total = success_count + failure_count
        trust = success_count / total if total > 0 else 0.5

        mobility_score = transition_model.stay_probability(current_state)
        social_trust = trust  # proxy when no co-location data exists
        reliability = 0.5 * trust + 0.5 * mobility_score

        node = FogNode(
            node_id=int(node_id),
            speed=avg_speed,
            trust_score=trust,
            mobility_score=mobility_score,
            reliability_score=reliability,
            transition_model=transition_model,
            social_trust=social_trust,
            centrality=centrality,
            current_state=current_state,
            past_success=success_count,
            past_failure=failure_count,
        )
        nodes.append(node)

    return nodes

