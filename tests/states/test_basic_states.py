from typing import Any
from typing import Dict
from typing import Tuple

import pytest

from cr_kyoushi.simulation import states
from cr_kyoushi.simulation import transitions


class NoneTransition(transitions.Transition):
    def __init__(self, name, target=None, asd=None):
        super().__init__(name, target=target)

    def execute_transition(self, current_state: str, context):
        return self.target


class StubState(states.State):
    def next(self, context):
        return None


@pytest.fixture()
def none_transitions() -> Tuple[
    NoneTransition, NoneTransition, NoneTransition, NoneTransition
]:
    t1 = NoneTransition(name="t1", target="t2")
    t2 = NoneTransition(name="t2", target="t3")
    t3 = NoneTransition(name="t3", target="t4")
    t4 = NoneTransition(name="t4", target=None)
    return (t1, t2, t3, t4)


def test_transition_map_init(
    none_transitions: Tuple[
        NoneTransition, NoneTransition, NoneTransition, NoneTransition
    ]
):
    (t1, t2, t3, t4) = none_transitions
    state = StubState("stub", [t1, t2, t3, t4])

    expected_dict = {t1.name: t1, t2.name: t2, t3.name: t3, t4.name: t4}
    assert state.transitions == list(none_transitions)
    assert state.transitions_map == expected_dict


def test_non_unique_transitions_fail(
    none_transitions: Tuple[
        NoneTransition, NoneTransition, NoneTransition, NoneTransition
    ]
):
    (t1, t2, t3, t4) = none_transitions

    # should raise error sind transition 1 is present twice
    with pytest.raises(ValueError):
        StubState(
            name="stub",
            transitions=[t1, t2, t3, t4, t1],
        )


def test_sequential_given_no_transition_raises_error():
    with pytest.raises(ValueError):
        states.SequentialState("test", None)


def test_sequential_state_given_transition_returns_it():
    abc = NoneTransition(name="none", target=None)
    seq = states.SequentialState("test", abc)

    # check transition property
    assert len(seq.transitions) == 1
    assert seq.transitions == [abc]

    # check next behaving as expected
    assert seq.next(None) == abc
    assert seq.next({"dummy": "context"}) == abc


def test_final_state_has_no_transition():
    final = states.FinalState("test")

    # check transition property
    assert len(final.transitions) == 0
    assert final.transitions == []

    # check next behaving as expected
    assert final.next(None) is None
    assert final.next({"dummy": "context"}) is None


def test_round_robin_loops(none_transitions):
    (t1, t2, t3, t4) = none_transitions

    transitions_list = [t1, t2, t3, t4]

    robin = states.RoundRobinState("test", transitions_list)
    empty_context: Dict[str, Any] = {}

    # verify initialization
    assert robin.name == "test"
    assert len(robin.transitions) == len(transitions_list)
    assert robin.transitions == transitions_list

    # verify round robin logic on next
    for _ in range(0, 10):
        assert robin.next(empty_context) == t1
        assert robin.next(empty_context) == t2
        assert robin.next(empty_context) == t3
        assert robin.next(empty_context) == t4

    # sanity check that one more next will get us to the start again
    assert robin.next(empty_context) == t1


def test_round_robin_no_transitions():
    robin = states.RoundRobinState("test", [])
    empty_context: Dict[str, Any] = {}

    # verify initialization
    assert robin.name == "test"
    assert len(robin.transitions) == 0
    assert robin.transitions == []

    # verify next will return none
    assert robin.next(empty_context) is None
    assert robin.next(empty_context) is None
