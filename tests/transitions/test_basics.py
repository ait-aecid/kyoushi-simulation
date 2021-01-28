from typing import (
    Any,
    Dict,
)

import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation import transitions
from cr_kyoushi.simulation.logging import get_logger

from ..fixtures.transitions import (
    Noop,
    noop,
)


log = get_logger()


@pytest.mark.parametrize(
    "func, name_input, expected_name",
    [
        pytest.param(noop, None, "noop", id="function-no-name"),
        pytest.param(Noop(), None, "noop", id="obj-no-name"),
        pytest.param(noop, "custom", "custom", id="function-no-name"),
        pytest.param(Noop(), "custom", "custom", id="obj-no-name"),
    ],
)
def test_transition_nameing(func, name_input, expected_name):
    transition = transitions.Transition(func, name=name_input)

    assert transition.transition_function == func
    assert transition.name == expected_name


@pytest.mark.parametrize(
    "func, decorator, expected_transition",
    [
        pytest.param(
            noop, transitions.transition, transitions.Transition, id="transition-func"
        ),
        pytest.param(
            Noop(), transitions.transition, transitions.Transition, id="transition-obj"
        ),
        pytest.param(
            noop,
            transitions.delayed_transition,
            transitions.DelayedTransition,
            id="delayed-func",
        ),
        pytest.param(
            Noop(),
            transitions.delayed_transition,
            transitions.DelayedTransition,
            id="delayed-obj",
        ),
    ],
)
def test_transition_decorator(func, decorator, expected_transition):

    transition = decorator()(func)

    assert transition.transition_function == func
    assert isinstance(transition, expected_transition)


def test_noop_transition(mocker: MockFixture):

    empty_context: Dict[str, Any] = {}
    current_state = "source"
    expected_state = "target"

    # mock the noop function so we can spy on it
    mock_noop = mocker.Mock()
    mocker.patch("cr_kyoushi.simulation.transitions.noop", mock_noop)

    noop_transition = transitions.NoopTransition(target=expected_state)

    # check that expected state is returned and noop was called
    assert noop_transition.execute(log, current_state, empty_context) == expected_state
    assert mock_noop.mock_calls == [
        mocker.call(
            log,
            current_state,
            empty_context,
            expected_state,
        )
    ]
