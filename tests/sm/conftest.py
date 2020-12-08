from typing import List
from typing import Optional

import pytest

from cr_kyoushi.simulation.errors import TransitionExecutionError
from cr_kyoushi.simulation.model import Context
from cr_kyoushi.simulation.states import SequentialState
from cr_kyoushi.simulation.states import State
from cr_kyoushi.simulation.transitions import Transition


class TransitionStub(Transition):
    def execute(self, current_state: str, context: Context):
        return self.target


class ExceptionTransitionStub(Transition):
    def execute(self, current_state: str, context: Context):
        raise Exception("Impossible transition")


class FallbackTransitionStub(Transition):
    def __init__(
        self,
        name: str,
        target: Optional[str],
        fallback_state: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        super().__init__(name, target)
        self.fallback_state = fallback_state
        self.cause = cause

    def execute(self, current_state: str, context: Context):
        raise TransitionExecutionError(
            message="Transition failed!",
            cause=self.cause,
            fallback_state=self.fallback_state,
        )


@pytest.fixture(scope="module")
def empty_transition() -> List[State]:
    transition1 = TransitionStub("move from 1 to 2", "state2")
    transition2 = TransitionStub("move from 2 to 3", "state3")

    state1 = SequentialState("state1", transition1)
    state2 = SequentialState("state2", transition2)
    state3 = SequentialState("state3", None)

    return [state1, state2, state3]


@pytest.fixture(scope="module")
def three_sequential_states() -> List[State]:
    transition1 = TransitionStub("move from 1 to 2", "state2")
    transition2 = TransitionStub("move from 2 to 3", "state3")
    transition3 = TransitionStub("move from 3 to end", None)

    state1 = SequentialState("state1", transition1)
    state2 = SequentialState("state2", transition2)
    state3 = SequentialState("state3", transition3)

    return [state1, state2, state3]


@pytest.fixture(scope="module")
def second_transition_fails() -> List[State]:
    transition1 = TransitionStub("move from 1 to 2", "state2")
    transition2 = ExceptionTransitionStub("fail to move from 2 to 3", "state3")
    transition3 = TransitionStub("move from 3 to end", None)

    state1 = SequentialState("state1", transition1)
    state2 = SequentialState("state2", transition2)
    state3 = SequentialState("state3", transition3)

    return [state1, state2, state3]


@pytest.fixture(scope="module")
def second_transition_error_fallback() -> List[State]:
    transition1 = TransitionStub("move from 1 to 2", "state2")
    transition2 = FallbackTransitionStub(
        "fail to move from 2 to 3",
        "state3",
        fallback_state="fallback",
        cause=Exception("Failed"),
    )
    transition3 = TransitionStub("move from 3 to end", None)
    fallback_transition = TransitionStub("move from fallback to end", None)

    state1 = SequentialState("state1", transition1)
    state2 = SequentialState("state2", transition2)
    state3 = SequentialState("state3", transition3)
    fallback = SequentialState("fallback", fallback_transition)

    return [state1, state2, state3, fallback]
