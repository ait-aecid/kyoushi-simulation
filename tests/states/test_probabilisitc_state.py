from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation.states import ProbabilisticState
from cr_kyoushi.simulation.transitions import Transition


@pytest.fixture()
def four_mocked_transitions(mocker: MockFixture) -> List[Transition]:
    mock_transition1 = mocker.Mock(spec=Transition)
    mock_transition1.name = "t1"

    mock_transition2 = mocker.Mock(spec=Transition)
    mock_transition2.name = "t2"

    mock_transition3 = mocker.Mock(spec=Transition)
    mock_transition3.name = "t3"

    mock_transition4 = mocker.Mock(spec=Transition)
    mock_transition4.name = "t4"

    return [mock_transition1, mock_transition2, mock_transition3, mock_transition4]


@pytest.fixture()
def four_uneven_weights_float(
    four_mocked_transitions: List[Transition],
) -> Tuple[List[Transition], List[float]]:
    # sums to 1.1 -> uneven probabilities
    return (four_mocked_transitions, [0.5, 0.2, 0.2, 0.2])


@pytest.fixture()
def four_uneven_weights_int(
    four_mocked_transitions: List[Transition],
) -> Tuple[List[Transition], List[int]]:
    # sums to 95 -> uneven probabilities
    return (four_mocked_transitions, [50, 20, 20, 5])


def test_empty_transition_list():
    transitions: List[Transition] = []
    weights: List[int] = []
    empty_context: Dict[str, Any] = {}

    state = ProbabilisticState(name="test", transitions=transitions, weights=weights)

    assert state.next(context=empty_context) is None


def test_non_unique_transitions_fail(four_mocked_transitions: List[Transition]):
    transitions = four_mocked_transitions + [four_mocked_transitions[0]]
    # sums to 100 -> is even
    weights = [20, 20, 20, 20, 20]

    # should raise error sind transition 1 is present twice
    with pytest.raises(ValueError):
        ProbabilisticState(name="test", transitions=transitions, weights=weights)


def test_uneven_probabilities_verification_fail_float(
    four_uneven_weights_float: List[float],
) -> ProbabilisticState:
    (transitions, weights) = four_uneven_weights_float

    with pytest.raises(ValueError):
        ProbabilisticState(name="test", transitions=transitions, weights=weights)


def test_uneven_probabilities_verification_fail_int(
    four_uneven_weights_int: List[float],
) -> ProbabilisticState:
    (transitions, weights) = four_uneven_weights_int

    with pytest.raises(ValueError):
        ProbabilisticState(name="test", transitions=transitions, weights=weights)


def test_weight_len_mismatch(four_mocked_transitions: List[Transition]):
    # sums to 100 so probs are even
    weights_less = [50, 50]

    # check len(weights)<len(transitions)
    assert len(four_mocked_transitions) != len(weights_less)
    with pytest.raises(ValueError):
        ProbabilisticState(
            name="test", transitions=four_mocked_transitions, weights=weights_less
        )

    # sums to 100 so probs are even
    weights_more = [20, 20, 20, 20, 20]
    # check len(weights)>len(transitions)
    assert len(four_mocked_transitions) != len(weights_more)
    with pytest.raises(ValueError):
        ProbabilisticState(
            name="test", transitions=four_mocked_transitions, weights=weights_more
        )


def test_next_probabilities_float(four_mocked_transitions: List[Transition]):
    weights = [0.3, 0.2, 0.4, 0.1]

    state = ProbabilisticState(
        name="test", transitions=four_mocked_transitions, weights=weights
    )
    empty_context: Dict[str, Any] = {}

    t1_name = four_mocked_transitions[0].name
    t2_name = four_mocked_transitions[1].name
    t3_name = four_mocked_transitions[2].name
    t4_name = four_mocked_transitions[3].name

    observed_counts = {
        t1_name: 0,
        t2_name: 0,
        t3_name: 0,
        t4_name: 0,
    }
    observations = 100000

    for i in range(0, observations):
        observed_transition = state.next(context=empty_context)
        # increase the observation count for the observed transition
        observed_counts[observed_transition.name] = (
            observed_counts[observed_transition.name] + 1
        )

    # we round observations to the first decimal place
    observed_probabilities = {
        t1_name: round(observed_counts[t1_name] / observations, 1),
        t2_name: round(observed_counts[t2_name] / observations, 1),
        t3_name: round(observed_counts[t3_name] / observations, 1),
        t4_name: round(observed_counts[t4_name] / observations, 1),
    }

    assert observed_probabilities[t1_name] == weights[0]
    assert observed_probabilities[t2_name] == weights[1]
    assert observed_probabilities[t3_name] == weights[2]
    assert observed_probabilities[t4_name] == weights[3]


def test_next_probabilities_int(four_mocked_transitions: List[Transition]):
    weights = [30, 20, 40, 10]

    state = ProbabilisticState(
        name="test", transitions=four_mocked_transitions, weights=weights
    )
    empty_context: Dict[str, Any] = {}

    t1_name = four_mocked_transitions[0].name
    t2_name = four_mocked_transitions[1].name
    t3_name = four_mocked_transitions[2].name
    t4_name = four_mocked_transitions[3].name

    observed_counts = {
        t1_name: 0,
        t2_name: 0,
        t3_name: 0,
        t4_name: 0,
    }
    observations = 100000

    for i in range(0, observations):
        observed_transition = state.next(context=empty_context)
        # increase the observation count for the observed transition
        observed_counts[observed_transition.name] = (
            observed_counts[observed_transition.name] + 1
        )

    # we round observations to the first decimal place
    observed_probabilities = {
        t1_name: round(observed_counts[t1_name] / observations, 1) * 100,
        t2_name: round(observed_counts[t2_name] / observations, 1) * 100,
        t3_name: round(observed_counts[t3_name] / observations, 1) * 100,
        t4_name: round(observed_counts[t4_name] / observations, 1) * 100,
    }

    assert observed_probabilities[t1_name] == weights[0]
    assert observed_probabilities[t2_name] == weights[1]
    assert observed_probabilities[t3_name] == weights[2]
    assert observed_probabilities[t4_name] == weights[3]