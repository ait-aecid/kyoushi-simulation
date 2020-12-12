from typing import List
from typing import Optional

import pytest

from cr_kyoushi.simulation.errors import TransitionExecutionError
from cr_kyoushi.simulation.model import Context
from cr_kyoushi.simulation.states import FinalState
from cr_kyoushi.simulation.states import SequentialState
from cr_kyoushi.simulation.states import State
from cr_kyoushi.simulation.transitions import Transition


def noop(current_state: str, context: Context):
    pass


def exception_function_stub(current_state: str, context: Context):
    raise Exception("Impossible transition")


class FallbackFunctionStub:
    def __init__(
        self,
        fallback_state: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        self.fallback_state = fallback_state
        self.cause = cause

    def __call__(self, current_state: str, context: Context):
        raise TransitionExecutionError(
            message="Transition failed!",
            cause=self.cause,
            fallback_state=self.fallback_state,
        )


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
