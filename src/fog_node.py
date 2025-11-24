"""
Fog node model storing trust, mobility, and reliability attributes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .mobility_predictor import TransitionModel, discretize_speed
from .trust_manager import update_trust as _update_trust


@dataclass
class FogNode:
    """Represents a vehicle participating in the fog network."""

    node_id: int
    speed: float
    trust_score: float
    mobility_score: float
    reliability_score: float
    transition_model: TransitionModel
    social_trust: float
    centrality: float
    current_state: str = field(default="MEDIUM")
    past_success: int = field(default=0)
    past_failure: int = field(default=0)

    def __post_init__(self) -> None:
        self.trust_score = min(max(self.trust_score, 0.0), 1.0)
        self.mobility_score = min(max(self.mobility_score, 0.0), 1.0)
        self.reliability_score = self.compute_reliability()
        self._initial_trust = self.trust_score
        self._initial_mobility = self.mobility_score
        self._initial_reliability = self.reliability_score
        self.current_state = discretize_speed(self.speed) if not self.current_state else self.current_state
        self.successes = self.past_success
        self.failures = self.past_failure

    # ------------------------------------------------------------------
    # Core metrics
    # ------------------------------------------------------------------
    def compute_mobility_score(self) -> float:
        """Update mobility using the stored transition model."""
        self.mobility_score = self.transition_model.stay_probability(self.current_state)
        return self.mobility_score

    def compute_reliability(self, trust_weight: float = 0.5, mobility_weight: float = 0.5) -> float:
        """Compute reliability as weighted combination of trust and mobility."""
        self.reliability_score = trust_weight * self.trust_score + mobility_weight * self.mobility_score
        return self.reliability_score

    def update_trust(self, success: bool, inc: float = 0.05, dec: float = 0.10) -> None:
        """Update trust/reliability based on execution outcome."""
        self.trust_score = _update_trust(self.trust_score, success, inc=inc, dec=dec)
        if success:
            self.successes += 1
        else:
            self.failures += 1
        self.compute_reliability()

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Reset node state to its initial metrics."""
        self.trust_score = self._initial_trust
        self.mobility_score = self._initial_mobility
        self.reliability_score = self._initial_reliability
        self.current_state = discretize_speed(self.speed)
        self.successes = self.past_success
        self.failures = self.past_failure

    def clone(self) -> "FogNode":
        """Create a detached copy to avoid sharing state between schedulers."""
        return FogNode(
            node_id=self.node_id,
            speed=self.speed,
            trust_score=self.trust_score,
            mobility_score=self.mobility_score,
            reliability_score=self.reliability_score,
            transition_model=self.transition_model,
            social_trust=self.social_trust,
            centrality=self.centrality,
            current_state=self.current_state,
            past_success=self.past_success,
            past_failure=self.past_failure,
        )

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "trust": self.trust_score,
            "mobility": self.mobility_score,
            "reliability": self.reliability_score,
            "social_trust": self.social_trust,
            "centrality": self.centrality,
            "successes": self.successes,
            "failures": self.failures,
        }

    def __repr__(self) -> str:
        return (
            f"FogNode(id={self.node_id}, trust={self.trust_score:.2f}, "
            f"mobility={self.mobility_score:.2f}, reliability={self.reliability_score:.2f})"
        )


