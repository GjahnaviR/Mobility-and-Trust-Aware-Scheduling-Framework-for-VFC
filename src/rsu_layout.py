"""
Helpers for modelling roadside fog servers / RSUs.

In many vehicular fog computing scenarios, it is assumed that there is a
roadside unit (RSU) or fog server deployed roughly every kilometre along
the road.  This module provides simple utilities to synthesise such RSU
nodes on top of the existing vehicle-derived `FogNode` set.

Design goals:
- Keep the core simulator and schedulers unchanged.
- Represent RSUs using the existing `FogNode` dataclass, flagged with
  `is_rsu=True` and an associated `position_km`.
- Allow callers (e.g. `main.py`) to easily augment the node list with
  "one RSU per kilometre" of roadway.
"""

from __future__ import annotations

from typing import List, Optional

from .fog_node import FogNode
from .mobility_predictor import TransitionModel, build_transition_model


def _default_rsu_transition_model() -> TransitionModel:
    """Return a high-stability transition model for stationary RSUs.

    RSUs are assumed to be stationary, so their mobility state should be
    very stable (high probability of remaining in the same state).
    """
    # Construct a small synthetic speed history with almost no variance.
    speeds = [0.0, 0.0, 0.0, 0.0]
    return build_transition_model(speeds)


def create_rsus_along_road(
    length_km: float,
    spacing_km: float = 1.0,
    start_id: int = 100_000,
    base_trust: float = 0.98,
    base_mobility: float = 0.99,
) -> List[FogNode]:
    """Create one RSU `FogNode` approximately every `spacing_km`.

    Parameters
    ----------
    length_km:
        Total length of the road segment being modelled.
    spacing_km:
        Distance between consecutive RSUs (defaults to 1 km).
    start_id:
        Node id offset for RSUs to avoid clashing with vehicle ids.
    base_trust, base_mobility:
        Baseline trust and mobility scores for RSUs.  RSUs are expected
        to be reliable and stationary, so both are relatively high.
    """
    if length_km <= 0:
        return []

    transition_model = _default_rsu_transition_model()
    rsus: List[FogNode] = []

    num_rsus = max(1, int(length_km // spacing_km) + 1)
    for index in range(num_rsus):
        position_km = index * spacing_km
        reliability = 0.5 * base_trust + 0.5 * base_mobility

        rsu = FogNode(
            node_id=start_id + index,
            speed=0.0,  # stationary RSU
            trust_score=base_trust,
            mobility_score=base_mobility,
            reliability_score=reliability,
            transition_model=transition_model,
            social_trust=base_trust,
            centrality=1.0,  # RSUs are typically well-connected
            current_state="SLOW",
            past_success=100,
            past_failure=5,
            position_km=position_km,
            is_rsu=True,
        )
        rsus.append(rsu)

    return rsus


def augment_with_rsus(
    nodes: List[FogNode],
    length_km: Optional[float] = None,
    spacing_km: float = 1.0,
) -> List[FogNode]:
    """Return a new list containing the original nodes plus RSUs.

    By default, the length of the road is approximated from the number
    of existing nodes if `length_km` is not supplied, assuming roughly
    one vehicle per kilometre.  You can override this by passing an
    explicit `length_km` from your scenario configuration.
    """
    if not nodes and length_km is None:
        # Nothing to base the layout on; return empty list.
        return []

    if length_km is None:
        # Fallback heuristic: approximate the road length (km) by the
        # number of distinct vehicle nodes.
        length_km = float(max(1, len(nodes)))

    max_existing_id = max(node.node_id for node in nodes) if nodes else 0
    rsus = create_rsus_along_road(
        length_km=length_km,
        spacing_km=spacing_km,
        start_id=max_existing_id + 1,
    )

    # Return a combined list: vehicles + RSUs
    return list(nodes) + rsus

