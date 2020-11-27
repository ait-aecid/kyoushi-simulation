from typing import List
from typing import Optional

import pytest

from cr_kyoushi.simulation.core.errors import TransitionExecutionError
from cr_kyoushi.simulation.core.sm import Context
from cr_kyoushi.simulation.core.sm import State
from cr_kyoushi.simulation.core.sm import Transition


class TransitionStub(Transition):
    @property
    def name(self) -> str:
        return self._name

    @property
    def target(self) -> Optional[str]:
        return self._target

    def __init__(self, name: str, target: Optional[str]):
        self._name = name
        self._target = target

    def execute(self, current_state: str, context: Context):
        return self.target


class ExceptionTransitionStub(Transition):
    @property
    def name(self) -> str:
        return self._name

    @property
    def target(self) -> Optional[str]:
        return self._target

    def __init__(self, name: str, target: Optional[str]):
        self._name = name
        self._target = target

    def execute(self, current_state: str, context: Context):
        raise Exception("Impossible transition")


class FallbackTransitionStub(Transition):
    @property
    def name(self) -> str:
        return self._name

    @property
    def target(self) -> Optional[str]:
        return self._target

    def __init__(
        self,
        name: str,
        target: Optional[str],
        fallback_state: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        self._name = name
        self._target = target
        self.fallback_state = fallback_state
        self.cause = cause

    def execute(self, current_state: str, context: Context):
        raise TransitionExecutionError(
            message="Transition failed!",
            cause=self.cause,
            fallback_state=self.fallback_state,
        )


class StateStub(State):
    @property
    def name(self) -> str:
        return self._name

    @property
    def transitions(self) -> List[Transition]:
        return [self._transition]

    def __init__(self, name: str, transition: Optional[Transition]):
        self._name = name
        self._transition = transition

    def next(self, context: Context):
        return self._transition


@pytest.fixture(scope="module")
def empty_transition() -> List[State]:
    transition1 = TransitionStub("move from 1 to 2", "state2")
    transition2 = TransitionStub("move from 2 to 3", "state3")

    state1 = StateStub("state1", transition1)
    state2 = StateStub("state2", transition2)
    state3 = StateStub("state3", None)

    return [state1, state2, state3]


@pytest.fixture(scope="module")
def three_sequential_states() -> List[State]:
    transition1 = TransitionStub("move from 1 to 2", "state2")
    transition2 = TransitionStub("move from 2 to 3", "state3")
    transition3 = TransitionStub("move from 3 to end", None)

    state1 = StateStub("state1", transition1)
    state2 = StateStub("state2", transition2)
    state3 = StateStub("state3", transition3)

    return [state1, state2, state3]


@pytest.fixture(scope="module")
def second_transition_fails() -> List[State]:
    transition1 = TransitionStub("move from 1 to 2", "state2")
    transition2 = ExceptionTransitionStub("fail to move from 2 to 3", "state3")
    transition3 = TransitionStub("move from 3 to end", None)

    state1 = StateStub("state1", transition1)
    state2 = StateStub("state2", transition2)
    state3 = StateStub("state3", transition3)

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

    state1 = StateStub("state1", transition1)
    state2 = StateStub("state2", transition2)
    state3 = StateStub("state3", transition3)
    fallback = StateStub("fallback", fallback_transition)

    return [state1, state2, state3, fallback]
