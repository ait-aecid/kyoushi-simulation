from typing import (
    Any,
    Callable,
    Dict,
    Tuple,
)

import pytest

from structlog.stdlib import BoundLogger

from cr_kyoushi.simulation import states
from cr_kyoushi.simulation.logging import get_logger
from cr_kyoushi.simulation.model import Context
from cr_kyoushi.simulation.transitions import Transition

from ..fixtures.transitions import noop


log = get_logger()


class StubState(states.State):
    def next(self, log, context):
        return None


@pytest.fixture()
def noop_transitions() -> Tuple[Transition, Transition, Transition, Transition]:
    t1 = Transition(name="t1", transition_function=noop, target="t2")
    t2 = Transition(name="t2", transition_function=noop, target="t3")
    t3 = Transition(name="t3", transition_function=noop, target="t4")
    t4 = Transition(name="t4", transition_function=noop, target=None)
    return (t1, t2, t3, t4)


def test_transition_map_init(
    noop_transitions: Tuple[Transition, Transition, Transition, Transition]
):
    (t1, t2, t3, t4) = noop_transitions
    state = StubState("stub", [t1, t2, t3, t4])

    expected_dict = {t1.name: t1, t2.name: t2, t3.name: t3, t4.name: t4}
    assert state.transitions == list(noop_transitions)
    assert state.transitions_map == expected_dict


def test_non_unique_transitions_fail(
    noop_transitions: Tuple[Transition, Transition, Transition, Transition]
):
    (t1, t2, t3, t4) = noop_transitions

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
    abc = Transition(name="none", transition_function=noop, target=None)
    seq = states.SequentialState("test", abc)

    # check transition property
    assert len(seq.transitions) == 1
    assert seq.transitions == [abc]

    # check next behaving as expected
    assert seq.next(log, None) == abc
    assert seq.next(log, {"dummy": "context"}) == abc


def test_final_state_has_no_transition():
    final = states.FinalState("test")

    # check transition property
    assert len(final.transitions) == 0
    assert final.transitions == []

    # check next behaving as expected
    assert final.next(log, None) is None
    assert final.next(log, {"dummy": "context"}) is None


def test_round_robin_loops(noop_transitions):
    (t1, t2, t3, t4) = noop_transitions

    transitions_list = [t1, t2, t3, t4]

    robin = states.RoundRobinState("test", transitions_list)
    empty_context: Dict[str, Any] = {}

    # verify initialization
    assert robin.name == "test"
    assert len(robin.transitions) == len(transitions_list)
    assert robin.transitions == transitions_list

    # verify round robin logic on next
    for _ in range(0, 10):
        assert robin.next(log, empty_context) == t1
        assert robin.next(log, empty_context) == t2
        assert robin.next(log, empty_context) == t3
        assert robin.next(log, empty_context) == t4

    # sanity check that one more next will get us to the start again
    assert robin.next(log, empty_context) == t1


def test_round_robin_no_transitions():
    robin = states.RoundRobinState("test", [])
    empty_context: Dict[str, Any] = {}

    # verify initialization
    assert robin.name == "test"
    assert len(robin.transitions) == 0
    assert robin.transitions == []

    # verify next will return none
    assert robin.next(log, empty_context) is None
    assert robin.next(log, empty_context) is None


@pytest.mark.parametrize(
    "decision, yes, no, expected",
    [
        pytest.param((lambda log, context: True), 0, 1, 0, id="yes"),
        pytest.param((lambda log, context: False), 0, 1, 1, id="no"),
    ],
)
def test_choice_returns_correctly(
    decision: Callable[[BoundLogger, Context], bool],
    yes: int,
    no: int,
    expected: int,
    noop_transitions,
):
    empty_context: Dict[str, Any] = {}

    state = states.ChoiceState(
        name="test",
        decision_function=decision,
        yes=noop_transitions[yes],
        no=noop_transitions[no],
    )

    assert state.next(log, empty_context) == noop_transitions[expected]
