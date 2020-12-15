from typing import List

import pytest

from cr_kyoushi.simulation.states import FinalState
from cr_kyoushi.simulation.states import SequentialState
from cr_kyoushi.simulation.states import State
from cr_kyoushi.simulation.transitions import Transition

from ..fixtures.transitions import FallbackFunctionStub
from ..fixtures.transitions import exception_function_stub
from ..fixtures.transitions import noop


@pytest.fixture(scope="module")
def empty_transition() -> List[State]:
    transition1 = Transition("move from 1 to 2", noop, "state2")
    transition2 = Transition("move from 2 to 3", noop, "state3")

    state1 = SequentialState("state1", transition1)
    state2 = SequentialState("state2", transition2)
    state3 = FinalState("state3")

    return [state1, state2, state3]


@pytest.fixture(scope="module")
def three_sequential_states() -> List[State]:
    transition1 = Transition("move from 1 to 2", noop, "state2")
    transition2 = Transition("move from 2 to 3", noop, "state3")
    transition3 = Transition("move from 3 to end", noop, None)

    state1 = SequentialState("state1", transition1)
    state2 = SequentialState("state2", transition2)
    state3 = SequentialState("state3", transition3)

    return [state1, state2, state3]


@pytest.fixture(scope="module")
def second_transition_fails() -> List[State]:
    transition1 = Transition("move from 1 to 2", noop, "state2")
    transition2 = Transition(
        "fail to move from 2 to 3", exception_function_stub, "state3"
    )
    transition3 = Transition("move from 3 to end", noop, None)

    state1 = SequentialState("state1", transition1)
    state2 = SequentialState("state2", transition2)
    state3 = SequentialState("state3", transition3)

    return [state1, state2, state3]


@pytest.fixture(scope="module")
def second_transition_error_fallback() -> List[State]:
    fallback_function = FallbackFunctionStub(
        fallback_state="fallback",
        cause=Exception("Failed"),
    )

    transition1 = Transition("move from 1 to 2", noop, "state2")
    transition2 = Transition("fail to move from 2 to 3", fallback_function, "state3")
    transition3 = Transition("move from 3 to end", noop, None)
    fallback_transition = Transition("move from fallback to end", noop, None)

    state1 = SequentialState("state1", transition1)
    state2 = SequentialState("state2", transition2)
    state3 = SequentialState("state3", transition3)
    fallback = SequentialState("fallback", fallback_transition)

    return [state1, state2, state3, fallback]
