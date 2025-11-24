"""
Mobility predictor based on a simple Markov Renewal Process (MRP).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import numpy as np
from sklearn.preprocessing import MinMaxScaler

STATE_LABELS = ["SLOW", "MEDIUM", "FAST"]


def discretize_speed(speed: float) -> str:
    """Map a numeric speed to one of the discrete mobility states."""
    if speed < 40:
        return "SLOW"
    if speed < 80:
        return "MEDIUM"
    return "FAST"


@dataclass
class TransitionModel:
    """Container for transition probabilities between mobility states."""

    matrix: np.ndarray  # shape (3, 3)
    state_index: Dict[str, int]

    def probability_of(self, from_state: str, to_state: str) -> float:
        i = self.state_index[from_state]
        j = self.state_index[to_state]
        return float(self.matrix[i, j])

    def stay_probability(self, current_state: str) -> float:
        """Probability of staying in SLOW or MEDIUM given current state."""
        i = self.state_index[current_state]
        stay_states = [self.state_index["SLOW"], self.state_index["MEDIUM"]]
        prob = float(self.matrix[i, stay_states[0]] + self.matrix[i, stay_states[1]])
        return min(max(prob, 0.0), 1.0)


def build_transition_model(speeds: Iterable[float]) -> TransitionModel:
    """Build a transition probability matrix from an iterable of speeds."""
    speeds = list(speeds)
    if len(speeds) < 2:
        # Synthesize a short trajectory to avoid division by zero
        speeds = speeds + speeds

    states = [discretize_speed(speed) for speed in speeds]
    state_index = {state: idx for idx, state in enumerate(STATE_LABELS)}
    counts = np.zeros((len(STATE_LABELS), len(STATE_LABELS)), dtype=float)

    for current, nxt in zip(states[:-1], states[1:]):
        counts[state_index[current], state_index[nxt]] += 1.0

    # Row-normalize; if a row sums to zero, fall back to a neutral prior.
    for i in range(counts.shape[0]):
        total = counts[i].sum()
        if total == 0:
            counts[i] = np.array([0.34, 0.33, 0.33])
        else:
            counts[i] /= total

    return TransitionModel(matrix=counts, state_index=state_index)


def normalize_speed_features(speeds: Iterable[float]) -> np.ndarray:
    """Return speeds scaled into [0, 1] using MinMax scaling."""
    arr = np.array(list(speeds), dtype=float).reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(arr)
    return scaled.flatten()

