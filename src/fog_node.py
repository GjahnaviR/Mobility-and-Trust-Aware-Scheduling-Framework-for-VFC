"""
Fog Node class for vehicular fog computing simulation.
Each node represents a vehicle with mobility, trust, and reliability metrics.
"""


class FogNode:
    """Represents a vehicular fog node with mobility, trust, and reliability scores."""
    
    def __init__(self, node_id: int, speed: float, success: int = 0, failure: int = 0):
        """
        Initialize a fog node from dataset.
        
        Args:
            node_id: Unique identifier for the node
            speed: Speed of the vehicle (higher speed = lower mobility score)
            success: Number of successful task executions (from dataset)
            failure: Number of failed task executions (from dataset)
        """
        self.node_id = node_id
        self.speed = speed
        # Store initial values for reset
        self._initial_success = success
        self._initial_failure = failure
        # Calculate initial trust from dataset: trust = success / (success + failure)
        total = success + failure
        if total > 0:
            self.initial_trust = success / total
        else:
            self.initial_trust = 0.5  # Default if no history
        self.initial_trust = max(0.0, min(1.0, self.initial_trust))  # Clamp between 0 and 1
        self.trust = self.initial_trust
        self._update_scores()
    
    def reset_to_initial(self):
        """Reset node to initial state (from dataset)."""
        self.trust = self.initial_trust
        self._update_scores()
    
    def _update_scores(self):
        """Update mobility and reliability scores based on current state."""
        # Mobility score: inverse of speed (lower speed = higher mobility score)
        self.mobility_score = 1.0 / self.speed if self.speed > 0 else 0.0
        
        # Reliability score: balanced combination of trust and mobility
        # Balanced weights allow trust updates to meaningfully improve reliability
        self.reliability_score = 0.5 * self.mobility_score + 0.5 * self.trust
    
    def update_trust_on_success(self):
        """Update trust value after successful task execution (+0.10)."""
        self.trust = min(1.0, self.trust + 0.10)
        self._update_scores()
    
    def update_trust_on_failure(self):
        """Update trust value after failed task execution (-0.15)."""
        self.trust = max(0.0, self.trust - 0.15)
        self._update_scores()
    
    def get_mobility_score(self) -> float:
        """Get the current mobility score."""
        return self.mobility_score
    
    def get_reliability_score(self) -> float:
        """Get the current reliability score."""
        return self.reliability_score
    
    def get_utility_score(self) -> float:
        """
        Calculate utility score for node selection.
        
        Utility = 0.4 * mobility + 0.3 * trust + 0.3 * reliability
        
        This combines multiple factors:
        - High mobility = node stays longer → fewer reassignments
        - High trust = node rarely fails → fewer retries
        - High reliability = faster completion
        
        Returns:
            Utility score for node selection
        """
        return 0.4 * self.mobility_score + 0.3 * self.trust + 0.3 * self.reliability_score
    
    def get_trust(self) -> float:
        """Get the current trust value."""
        return self.trust
    
    def __repr__(self):
        return (f"FogNode(id={self.node_id}, speed={self.speed:.2f}, "
                f"trust={self.trust:.2f}, mobility={self.mobility_score:.3f}, "
                f"reliability={self.reliability_score:.3f})")

