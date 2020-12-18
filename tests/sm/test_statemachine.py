from typing import List

import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation.sm import StartEndTimeStatemachine
from cr_kyoushi.simulation.sm import Statemachine
from cr_kyoushi.simulation.states import State


@pytest.mark.parametrize("sm_class", [Statemachine, StartEndTimeStatemachine])
def test_sequential_sm_execution_stops(
    sm_class,
    mocker: MockFixture,
    three_sequential_states: List[State],
):
    """This test checks if given sequential states the state machine executes each state once and then stops

    Args:
        mocker (MockFixture): pytest mocker fixture for mocking
        three_sequential_states (List[State]): test fixture containing a list of 3 sequentially linked states
    """
    state1 = three_sequential_states[0]
    transition1 = state1.transitions[0]

    state2 = three_sequential_states[1]
    transition2 = state2.transitions[0]

    state3 = three_sequential_states[2]
    transition3 = state3.transitions[0]

    # state spy setup
    state1_spy = mocker.spy(state1, "next")
    state2_spy = mocker.spy(state2, "next")
    state3_spy = mocker.spy(state3, "next")

    # transition spy setup
    transition1_spy = mocker.spy(transition1, "execute")
    transition2_spy = mocker.spy(transition2, "execute")
    transition3_spy = mocker.spy(transition3, "execute")

    sm = sm_class(
        initial_state=state1.name,
        states=three_sequential_states,
    )
    sm.run()

    # check that each states next is only called once
    assert state1_spy.call_count == 1
    assert state2_spy.call_count == 1
    assert state3_spy.call_count == 1

    # check that each transition is only executed once
    assert transition1_spy.call_count == 1
    assert transition2_spy.call_count == 1
    assert transition3_spy.call_count == 1


@pytest.mark.parametrize("sm_class", [Statemachine, StartEndTimeStatemachine])
def test_sequential_sm_execution_with_empty_transition(
    sm_class,
    mocker: MockFixture,
    empty_transition: List[State],
):
    """This test checks if given sequential states the state machine executes each state once and then stops

    Args:
        mocker (MockFixture): pytest mocker fixture for mocking
        empty_transition (List[State]): test fixture containing a list of 3 sequentially linked states
    """
    state1 = empty_transition[0]
    transition1 = state1.transitions[0]

    state2 = empty_transition[1]
    transition2 = state2.transitions[0]

    state3 = empty_transition[2]

    # state spy setup
    state1_spy = mocker.spy(state1, "next")
    state2_spy = mocker.spy(state2, "next")
    state3_spy = mocker.spy(state3, "next")

    # transition spy setup
    transition1_spy = mocker.spy(transition1, "execute")
    transition2_spy = mocker.spy(transition2, "execute")

    sm = sm_class(
        initial_state=state1.name,
        states=empty_transition,
    )
    sm.run()

    # check that the last state has no transitions
    assert len(state3.transitions) == 0

    # check that each states next is only called once
    assert state1_spy.call_count == 1
    assert state2_spy.call_count == 1
    assert state3_spy.call_count == 1

    # check that each transition is only executed once
    assert transition1_spy.call_count == 1
    assert transition2_spy.call_count == 1


@pytest.mark.parametrize("sm_class", [Statemachine, StartEndTimeStatemachine])
def test_sequential_sm_execution(
    sm_class,
    mocker: MockFixture,
    three_sequential_states: List[State],
):
    """This test checks if given sequential states the state machine executes each state in order

    Args:
        mocker (MockFixture): pytest mocker fixture for mocking
        three_sequential_states (List[State]): test fixture containing a list of 3 sequentially linked states
    """
    state1 = three_sequential_states[0]
    transition1 = state1.transitions[0]

    state2 = three_sequential_states[1]
    transition2 = state2.transitions[0]

    state3 = three_sequential_states[2]
    transition3 = state3.transitions[0]

    # state spy setup
    state1_spy = mocker.spy(state1, "next")
    state2_spy = mocker.spy(state2, "next")
    state3_spy = mocker.spy(state3, "next")

    # transition spy setup
    transition1_spy = mocker.spy(transition1, "execute")
    transition2_spy = mocker.spy(transition2, "execute")
    transition3_spy = mocker.spy(transition3, "execute")

    sm = sm_class(
        initial_state=state1.name,
        states=three_sequential_states,
    )

    execute_transition_spy = mocker.spy(sm, "_execute_transition")

    # check that no transition was executed by the sm
    assert execute_transition_spy.call_count == 0

    # check that each states next was not called yet
    assert state1_spy.call_count == 0
    assert state2_spy.call_count == 0
    assert state3_spy.call_count == 0

    # check that each transition was not called yet
    assert transition1_spy.call_count == 0
    assert transition2_spy.call_count == 0
    assert transition3_spy.call_count == 0

    sm._execute_step()

    # check that the first transition was executed
    assert execute_transition_spy.call_count == 1

    # check that only the first states next was called
    assert state1_spy.call_count == 1
    assert state2_spy.call_count == 0
    assert state3_spy.call_count == 0

    # check that only the first transition next was called
    assert transition1_spy.call_count == 1
    assert transition2_spy.call_count == 0
    assert transition3_spy.call_count == 0

    sm._execute_step()

    # check that the second transition was executed
    assert execute_transition_spy.call_count == 2

    # check that only the second states next was called
    assert state1_spy.call_count == 1
    assert state2_spy.call_count == 1
    assert state3_spy.call_count == 0

    # check that only the second transition was called
    assert transition1_spy.call_count == 1
    assert transition2_spy.call_count == 1
    assert transition3_spy.call_count == 0

    sm._execute_step()

    # check that the last transition was executed
    assert execute_transition_spy.call_count == 3

    # check that only the last states next was called
    assert state1_spy.call_count == 1
    assert state2_spy.call_count == 1
    assert state3_spy.call_count == 1

    # check that only the last transition was called
    assert transition1_spy.call_count == 1
    assert transition2_spy.call_count == 1
    assert transition3_spy.call_count == 1

    # assert that after the final state the current state is None
    assert sm.current_state is None


@pytest.mark.parametrize("sm_class", [Statemachine, StartEndTimeStatemachine])
def test_sequential_sm_execution_with_failing_state(
    sm_class,
    mocker: MockFixture,
    second_transition_fails: List[State],
):
    """This test checks if the state machine stops on a failing state if no recovery tries are available

    Args:
        mocker (MockFixture): pytest mocker fixture
        second_transition_fails (List[State]): sequential sm states with the second one always failing
    """
    state1 = second_transition_fails[0]
    transition1 = state1.transitions[0]

    state2 = second_transition_fails[1]
    transition2 = state2.transitions[0]

    state3 = second_transition_fails[2]
    transition3 = state3.transitions[0]

    # state spy setup
    state1_spy = mocker.spy(state1, "next")
    state2_spy = mocker.spy(state2, "next")
    state3_spy = mocker.spy(state3, "next")

    # transition spy setup
    transition1_spy = mocker.spy(transition1, "execute")
    transition2_spy = mocker.spy(transition2, "execute")
    transition3_spy = mocker.spy(transition3, "execute")

    sm = sm_class(
        initial_state=state1.name,
        states=second_transition_fails,
    )

    sm.run()

    # check that only state1 and state2 next where called
    # and state 3 was never reached due to the exception
    assert state1_spy.call_count == 1
    assert state2_spy.call_count == 1
    assert state3_spy.call_count == 0

    # check that only transition1 and transition2 where executed
    # and transition3 was never reach
    assert transition1_spy.call_count == 1
    assert transition2_spy.call_count == 1
    assert transition3_spy.call_count == 0


@pytest.mark.parametrize("sm_class", [Statemachine, StartEndTimeStatemachine])
def test_sequential_sm_execution_with_failing_state_recovery(
    sm_class,
    mocker: MockFixture,
    second_transition_fails: List[State],
):
    """This test checks if the state machine tries to recover from a failing state

    Args:
        mocker (MockFixture): pytest mocker fixture
        second_transition_fails (List[State]): sequential sm states with the second one always failing
    """
    state1 = second_transition_fails[0]
    transition1 = state1.transitions[0]

    state2 = second_transition_fails[1]
    transition2 = state2.transitions[0]

    state3 = second_transition_fails[2]
    transition3 = state3.transitions[0]

    # state spy setup
    state1_spy = mocker.spy(state1, "next")
    state2_spy = mocker.spy(state2, "next")
    state3_spy = mocker.spy(state3, "next")

    # transition spy setup
    transition1_spy = mocker.spy(transition1, "execute")
    transition2_spy = mocker.spy(transition2, "execute")
    transition3_spy = mocker.spy(transition3, "execute")

    sm = sm_class(
        initial_state=state1.name,
        states=second_transition_fails,
        max_errors=3,
    )

    execute_transition_spy = mocker.spy(sm, "_execute_transition")

    # check that no transition was executed by the sm
    assert execute_transition_spy.call_count == 0

    # check states are initially not called
    assert state1_spy.call_count == 0
    assert state2_spy.call_count == 0
    assert state3_spy.call_count == 0

    # check transitions are intially not called
    assert transition1_spy.call_count == 0
    assert transition2_spy.call_count == 0
    assert transition3_spy.call_count == 0

    # step 1
    sm._execute_step()

    # check that transition execution count has increased by one
    assert execute_transition_spy.call_count == 1

    # check that initial state next has be called
    assert state1_spy.call_count == 1
    assert state2_spy.call_count == 0
    assert state3_spy.call_count == 0

    # check that initial state transition has been called
    assert transition1_spy.call_count == 1
    assert transition2_spy.call_count == 0
    assert transition3_spy.call_count == 0

    # step 2 - error 1
    sm._execute_step()

    # check that transition execution count has increased by one
    assert execute_transition_spy.call_count == 2

    # check that state 2 next has be called
    assert state1_spy.call_count == 1
    assert state2_spy.call_count == 1
    assert state3_spy.call_count == 0

    # check that state 2 transition has been called
    assert transition1_spy.call_count == 1
    assert transition2_spy.call_count == 1
    assert transition3_spy.call_count == 0

    # assert that we recovered to initial state
    assert sm.current_state == sm.initial_state

    # step 3 - error 1
    sm._execute_step()

    # check that transition execution count has increased by one
    assert execute_transition_spy.call_count == 3

    # check that initial state next has be called
    assert state1_spy.call_count == 2
    assert state2_spy.call_count == 1
    assert state3_spy.call_count == 0

    # check that initial state transition has been called
    assert transition1_spy.call_count == 2
    assert transition2_spy.call_count == 1
    assert transition3_spy.call_count == 0

    # step 4 - error 2
    sm._execute_step()

    # check that transition execution count has increased by one
    assert execute_transition_spy.call_count == 4

    # check that state 2 next has be called
    assert state1_spy.call_count == 2
    assert state2_spy.call_count == 2
    assert state3_spy.call_count == 0

    # check that state 2 transition has been called
    assert transition1_spy.call_count == 2
    assert transition2_spy.call_count == 2
    assert transition3_spy.call_count == 0

    # assert that we recovered to initial state
    assert sm.current_state == sm.initial_state

    # step 5 - error 2
    sm._execute_step()

    # check that transition execution count has increased by one
    assert execute_transition_spy.call_count == 5

    # check that initial state next has be called
    assert state1_spy.call_count == 3
    assert state2_spy.call_count == 2
    assert state3_spy.call_count == 0

    # check that initial state transition has been called
    assert transition1_spy.call_count == 3
    assert transition2_spy.call_count == 2
    assert transition3_spy.call_count == 0

    # step 6 - error 3
    sm._execute_step()

    # check that transition execution count has increased by one
    assert execute_transition_spy.call_count == 6

    # check that state 2 next has be called
    assert state1_spy.call_count == 3
    assert state2_spy.call_count == 3
    assert state3_spy.call_count == 0

    # check that state 2 transition has been called
    assert transition1_spy.call_count == 3
    assert transition2_spy.call_count == 3
    assert transition3_spy.call_count == 0

    # assert that after the 3rd error we did not recover to initial state
    assert sm.current_state is None


@pytest.mark.parametrize("sm_class", [Statemachine, StartEndTimeStatemachine])
def test_sequential_sm_execution_with_transition_error(
    sm_class,
    mocker: MockFixture,
    second_transition_error_fallback: List[State],
):
    """This test checks if the state machine tries to recover from a failing state

    Args:
        mocker (MockFixture): pytest mocker fixture
        second_transition_error_fallback (List[State]): sequential sm states with the second one always failing
                                               into a transition execution error
    """
    state1 = second_transition_error_fallback[0]
    transition1 = state1.transitions[0]

    state2 = second_transition_error_fallback[1]
    transition2 = state2.transitions[0]

    state3 = second_transition_error_fallback[2]
    transition3 = state3.transitions[0]

    fallback = second_transition_error_fallback[3]
    fallback_transition = fallback.transitions[0]

    # state spy setup
    state1_spy = mocker.spy(state1, "next")
    state2_spy = mocker.spy(state2, "next")
    state3_spy = mocker.spy(state3, "next")
    fallback_spy = mocker.spy(fallback, "next")

    # transition spy setup
    transition1_spy = mocker.spy(transition1, "execute")
    transition2_spy = mocker.spy(transition2, "execute")
    transition3_spy = mocker.spy(transition3, "execute")
    fallaback_transition_spy = mocker.spy(fallback_transition, "execute")

    sm = Statemachine(
        initial_state=state1.name,
        states=second_transition_error_fallback,
    )

    sm.run()

    # check that only state1 and state2 next where called
    # and state 3 was never reached due to the exception
    assert state1_spy.call_count == 1
    assert state2_spy.call_count == 1
    assert state3_spy.call_count == 0
    assert fallback_spy.call_count == 1

    # check that only transition1 and transition2 where executed
    # and transition3 was never reach
    assert transition1_spy.call_count == 1
    assert transition2_spy.call_count == 1
    assert transition3_spy.call_count == 0
    assert fallaback_transition_spy.call_count == 1
