import numpy as np

from src.dag_manager import DAGManager
from src.fog_node import FogNode
from src.mobility_predictor import TransitionModel
from src.simulator import FailureSettings, Simulator
from src.task import Task


def _transition_model() -> TransitionModel:
    matrix = np.array(
        [
            [0.6, 0.3, 0.1],
            [0.2, 0.6, 0.2],
            [0.1, 0.3, 0.6],
        ]
    )
    return TransitionModel(matrix=matrix, state_index={"SLOW": 0, "MEDIUM": 1, "FAST": 2})


def _make_node(node_id: int, mobility: float, trust: float) -> FogNode:
    return FogNode(
        node_id=node_id,
        speed=50.0,
        trust_score=trust,
        mobility_score=mobility,
        reliability_score=0.5,
        transition_model=_transition_model(),
        social_trust=trust,
        centrality=0.5,
        current_state="MEDIUM",
    )


def test_reliability_bounded():
    node = _make_node(1, mobility=0.8, trust=0.9)
    reliability = node.compute_reliability()
    assert 0.0 <= reliability <= 1.0


def test_dag_respects_dependencies():
    tasks = [
        Task(task_id=1, execution_time=1.0, deps=[]),
        Task(task_id=2, execution_time=1.0, deps=[1]),
        Task(task_id=3, execution_time=1.0, deps=[2]),
    ]
    dag = DAGManager(tasks)
    ready = dag.get_ready_tasks(set())
    assert ready == [1]
    dag.get_task(1).mark_completed(1.0)
    ready_after = dag.get_ready_tasks({1})
    assert ready_after == [2]


def test_failure_probability_monotonic():
    simulator = Simulator(failure_settings=FailureSettings(slope=5.0, midpoint=0.25))
    low = simulator._failure_probability(0.1)
    high = simulator._failure_probability(0.9)
    assert low > high


