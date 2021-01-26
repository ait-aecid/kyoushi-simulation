import pytest

from cr_kyoushi.simulation import transitions

from ..fixtures.transitions import (
    Noop,
    noop,
)


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
