from datetime import (
    datetime,
    timedelta,
)

import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation.model import WorkSchedule
from cr_kyoushi.simulation.sm import WorkHoursStatemachine


def test_in_work_hours_given_no_schedule_returns_true():

    sm = WorkHoursStatemachine("mock", states=[])
    assert sm._in_work_hours() is True


@pytest.mark.parametrize("result", [True, False])
def test_in_work_hours_checks_correctly(result, mocker: MockFixture):
    call = mocker.call
    current_time = datetime.now()

    now_mock = mocker.Mock()
    now_mock.return_value = current_time
    mocker.patch("cr_kyoushi.simulation.sm.now", now_mock)

    schedule_mock = mocker.MagicMock(spec=WorkSchedule)
    schedule_mock.is_work_time.return_value = result

    sm = WorkHoursStatemachine("mock", states=[], work_schedule=schedule_mock)

    expected_calls = [call.is_work_time(current_time)]

    assert sm._in_work_hours() is result
    assert schedule_mock.is_work_time.mock_calls == expected_calls


def test_wait_for_work_given_no_schedule_do_nothing(mocker: MockFixture):
    sleep_mock = mocker.Mock()
    sleep_mock.return_value = None
    mocker.patch("cr_kyoushi.simulation.sm.sleep_until", sleep_mock)

    sm = WorkHoursStatemachine("mock", states=[])

    resume_spy = mocker.spy(sm, "_resume_work")

    sm._wait_for_work()

    assert sleep_mock.call_count == 0
    assert resume_spy.call_count == 0


@pytest.mark.parametrize(
    "end_time, next_work",
    [
        pytest.param(
            datetime(2020, 12, 19, 0, 0),
            None,
            id="no-next-work",
        ),
        pytest.param(
            datetime(2020, 12, 19, 0, 0),
            datetime(2020, 12, 20, 0, 0),
            id="end_time-before-work",
        ),
    ],
)
def test_wait_for_work_stops_machine_when_end_or_no_work(
    end_time,
    next_work,
    mocker: MockFixture,
):
    call = mocker.call

    sleep_mock = mocker.Mock()
    sleep_mock.return_value = None
    mocker.patch("cr_kyoushi.simulation.sm.sleep_until", sleep_mock)

    current_time = datetime.now()

    now_mock = mocker.Mock()
    now_mock.return_value = current_time
    mocker.patch("cr_kyoushi.simulation.sm.now", now_mock)

    schedule_mock = mocker.MagicMock(spec=WorkSchedule)
    schedule_mock.next_work_start.return_value = next_work

    sm = WorkHoursStatemachine(
        "mock", states=[], end_time=end_time, work_schedule=schedule_mock
    )

    resume_spy = mocker.spy(sm, "_resume_work")

    expected_schedule_calls = [call.next_work_start(current_time)]

    # check that we start in initial state
    assert sm.current_state == "mock"

    sm._wait_for_work()

    assert sm.current_state is None
    assert sleep_mock.call_count == 0
    assert resume_spy.call_count == 0
    assert schedule_mock.mock_calls == expected_schedule_calls


def test_wait_for_work_given_schedule_and_work_day_waits(mocker: MockFixture):
    end_time = datetime(2020, 12, 19, 12, 0)
    next_work = datetime(2020, 12, 19, 9, 0)

    call = mocker.call

    sleep_mock = mocker.Mock()
    sleep_mock.return_value = None
    mocker.patch("cr_kyoushi.simulation.sm.sleep_until", sleep_mock)

    current_time = datetime.now()

    now_mock = mocker.Mock()
    now_mock.return_value = current_time
    mocker.patch("cr_kyoushi.simulation.sm.now", now_mock)

    schedule_mock = mocker.MagicMock(spec=WorkSchedule)
    schedule_mock.next_work_start.return_value = next_work

    sm = WorkHoursStatemachine(
        "mock",
        states=[],
        end_time=end_time,
        work_schedule=schedule_mock,
    )

    resume_spy = mocker.spy(sm, "_resume_work")

    expected_schedule_calls = [call.next_work_start(current_time)]
    expected_sleep_calls = [call(next_work)]

    # check that we start in initial state
    assert sm.current_state == "mock"

    sm._wait_for_work()

    assert sm.current_state == "mock"
    assert sleep_mock.call_count == 1
    assert resume_spy.call_count == 1

    assert schedule_mock.mock_calls == expected_schedule_calls
    assert sleep_mock.mock_calls == expected_sleep_calls


@pytest.mark.parametrize(
    "is_work, exec_step_count, wait_count",
    [
        pytest.param(True, 1, 0, id="in-work-hours"),
        pytest.param(False, 0, 1, id="outside-work-hours"),
    ],
)
def testexecute_step(
    is_work,
    exec_step_count,
    wait_count,
    mocker: MockFixture,
):
    end_time = datetime.now() + timedelta(1)
    # mock the super execute_step method
    super_exec_mock = mocker.Mock()
    super_exec_mock.return_value = None
    mocker.patch("cr_kyoushi.simulation.sm.Statemachine.execute_step", super_exec_mock)

    schedule_mock = mocker.MagicMock(spec=WorkSchedule)

    sm = WorkHoursStatemachine(
        "mock",
        states=[],
        end_time=end_time,
        work_schedule=schedule_mock,
    )

    # mock the wait for work
    wait_mock = mocker.Mock()
    wait_mock.return_value = None
    mocker.patch.object(sm, "_wait_for_work", wait_mock)

    # mock in work hours
    check_work_mock = mocker.Mock()
    check_work_mock.return_value = is_work
    mocker.patch.object(sm, "_in_work_hours", check_work_mock)

    sm.execute_step()

    assert wait_mock.call_count == wait_count
    assert super_exec_mock.call_count == exec_step_count
