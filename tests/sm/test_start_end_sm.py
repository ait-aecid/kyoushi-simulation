import datetime

import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation.sm import StartEndTimeStatemachine


class DateTimeMock:
    """utility class for faking datetime.now() and sleep interaction"""

    def __init__(self, fake_datetimes):
        self.fake_datetimes = fake_datetimes
        self.index = 0

    def next(self):
        self.index = (self.index + 1) % len(self.fake_datetimes)

    def mock_now(self):
        return self.fake_datetimes[self.index]


@pytest.mark.parametrize(
    "datetimes, start_time",
    [
        pytest.param(
            datetime.datetime(2020, 12, 18, 12, 30),
            None,
            id="no-start-time",
        ),
        pytest.param(
            datetime.datetime(2020, 12, 18, 12, 30),
            datetime.datetime(2020, 12, 18, 12, 0),
            id="current-time-after-start",
        ),
        pytest.param(
            [
                datetime.datetime(2020, 12, 18, 11, 0),
                datetime.datetime(2020, 12, 18, 12, 0),
            ],
            datetime.datetime(2020, 12, 18, 12, 0),
            id="current-before-start",
        ),
    ],
)
def test_wait_for_start(
    datetimes,
    start_time,
    three_sequential_states,
    mocker: MockFixture,
    monkeypatch,
):
    call = mocker.call
    # create a mock datetime and replace the now function
    datetime_mock = mocker.MagicMock(wraps=datetime.datetime)
    datetime_mock.now.side_effect = datetimes

    # replace datetime.datetime with out mock
    # (we have to do it like this as it is a builtin)
    monkeypatch.setattr(datetime, "datetime", datetime_mock)

    # mock sleep_until
    sleep_mock = mocker.Mock()
    sleep_mock.return_value = None
    mocker.patch("cr_kyoushi.simulation.sm.sleep_until", sleep_mock)

    # mock sm._execute_machine
    exec_mock = mocker.Mock()
    exec_mock.return_value = None
    mocker.patch(
        "cr_kyoushi.simulation.sm.StartEndTimeStatemachine._execute_machine",
        exec_mock,
    )

    mock_parent = mocker.Mock()
    mock_parent.m1, mock_parent.m2 = sleep_mock, exec_mock

    sm = StartEndTimeStatemachine(
        three_sequential_states[0].name,
        states=three_sequential_states,
        start_time=start_time,
    )

    sm.run()

    # if start time is none we should have skipped the sleep until
    if start_time is None:
        mock_parent.assert_has_calls([call.m2()])
    # assert that sleep was called before executing the machine
    # and with correct start time
    else:
        mock_parent.assert_has_calls([call.m1(start_time), call.m2()])


def test_stop_on_end_time(mocker: MockFixture, monkeypatch):
    current_time = datetime.datetime.now()
    end_time = current_time + datetime.timedelta(1)

    fake_datetime = DateTimeMock([current_time, current_time, current_time, end_time])

    # mock sm._execute_step
    exec_mock = mocker.Mock()
    exec_mock.side_effect = fake_datetime.next
    mocker.patch(
        "cr_kyoushi.simulation.sm.StartEndTimeStatemachine._execute_step",
        exec_mock,
    )

    # create a mock datetime and replace the now function
    datetime_mock = mocker.MagicMock(wraps=datetime.datetime)
    datetime_mock.now.side_effect = fake_datetime.mock_now

    # replace datetime.datetime with out mock
    # (we have to do it like this as it is a builtin)
    monkeypatch.setattr(datetime, "datetime", datetime_mock)

    sm = StartEndTimeStatemachine(
        "mock-state",
        states=[],
        end_time=end_time,
    )

    # mock sm.current_state
    state_mock = mocker.patch.object(sm, "current_state")
    state_mock.return_value = "mock-state"

    sm.run()

    # verify that before the 4th exec sm end since end time was reached
    assert exec_mock.call_count == 3


def test_stop_on_end_state(three_sequential_states, mocker: MockFixture, monkeypatch):
    current_time = datetime.datetime.now()
    end_time = current_time + datetime.timedelta(1)

    # create a mock datetime and replace the now function
    # fix return value so end time can never be reached
    datetime_mock = mocker.MagicMock(wraps=datetime.datetime)
    datetime_mock.now.return_value = current_time

    # replace datetime.datetime with out mock
    # (we have to do it like this as it is a builtin)
    monkeypatch.setattr(datetime, "datetime", datetime_mock)

    sm = StartEndTimeStatemachine(
        three_sequential_states[0].name,
        states=three_sequential_states,
        end_time=end_time,
    )

    # spy on exec step so we can verify that we only executed our transitions
    exec_step_spy = mocker.spy(sm, "_execute_step")

    sm.run()

    # assert that we only exec 3 times since we end after the 3rd state
    assert exec_step_spy.call_count == 3
    assert sm.current_state is None
    assert sm._is_end_time() is False
