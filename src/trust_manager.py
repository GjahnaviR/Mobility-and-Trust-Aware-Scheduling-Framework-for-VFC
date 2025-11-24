"""
Utility helpers for managing trust scores.
"""

from __future__ import annotations


def update_trust(trust: float, success: bool, inc: float = 0.05, dec: float = 0.10) -> float:
    """Return an updated trust value bounded inside [0, 1]."""
    if success:
        trust += inc
    else:
        trust -= dec
    return min(max(trust, 0.0), 1.0)

