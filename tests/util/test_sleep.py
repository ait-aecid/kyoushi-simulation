import datetime
import time

import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation.model import ApproximateFloat
from cr_kyoushi.simulation.util import sleep
from cr_kyoushi.simulation.util import sleep_until


def test_sleep_waits():
    precission = 0.01
    expected_wait = 3

    # execute and time sleep
    start_seconds = time.time()
    sleep(expected_wait)
    end_seconds = time.time()

    # calculate waited time
    observed_wait = end_seconds - start_seconds

    assert abs(expected_wait - observed_wait) <= precission


def test_sleep_approximate_waits():
    precission = 0.01
    margin = 3
    min_wait = 3
    max_wait = 6
    approximate_wait = ApproximateFloat(min=min_wait, max=max_wait)

    # execute and time sleep
    start_seconds = time.time()
    sleep(approximate_wait)
    end_seconds = time.time()

    # calculate waited time
    observed_wait = end_seconds - start_seconds

    assert abs(min_wait - observed_wait) <= precission + margin


@pytest.mark.parametrize(
    "relative_endtime, epsilon, min_sleep_amount, sleep_amount",
    [
        # should be sleep 1.5, 0.75, 0.375, 0.1875, 0.1, 0,1
        pytest.param(3, 0.1, 0.1, None, id="log-default-settings"),
        # should be sleep 1.5, 1, 1
        pytest.param(3, 0.5, 1, None, id="log-custom-min-sleep"),
        # should be 1, 1, 1
        pytest.param(3.0, 0.1, 0.1, 1, id="fixed-default-settings"),
        # should be 1.5, 1.5
        pytest.param(3.0, 0.1, 1.5, 1, id="fixed-min-override"),
        # worst case is 1.5 + 1.499* + 1.5 so we oversleep 1.5s
        pytest.param(
            3.0,
            1.5,
            0.1,
            ApproximateFloat(min=1, max=1.5),
            id="fixed-approx-default-settings",
        ),
    ],
)
def test_wait_until(
    relative_endtime,
    epsilon,
    min_sleep_amount,
    sleep_amount,
    mocker: MockFixture,
    monkeypatch,
):
    start_time = datetime.datetime.now()
    # 15 seconds from now
    end_time = start_time + datetime.timedelta(0, relative_endtime)

    class SleepMock:
        """utility class for faking datetime.now() and sleep interaction"""

        def __init__(self, current_time):
            self.current_time = current_time
            self.time_slept = 0

        def mock_sleep(self, amount):
            # if sleep gets a approximate float get the current float value
            if isinstance(amount, ApproximateFloat):
                amount = amount.value
            self.time_slept = amount + self.time_slept
            # simulate sleep by simply adding to the fake current time
            self.current_time = self.current_time + datetime.timedelta(0, amount)

        def mock_now(self):
            # just return the fake current time
            print(self.current_time)
            return self.current_time

    mock_obj = SleepMock(start_time)

    # mock the sleep function
    sleep_mock = mocker.Mock()
    sleep_mock.side_effect = mock_obj.mock_sleep
    mocker.patch("cr_kyoushi.simulation.util.sleep", sleep_mock)

    # create a mock datetime and replace the now function
    datetime_mock = mocker.MagicMock(wraps=datetime.datetime)
    datetime_mock.now.side_effect = mock_obj.mock_now

    # replace datetime.datetime with out mock
    # (we have to do it like this as it is a builtin)
    monkeypatch.setattr(datetime, "datetime", datetime_mock)

    sleep_until(
        end_time,
        min_sleep_amount=min_sleep_amount,
        sleep_amount=sleep_amount,
    )

    # verify that slept until end time
    assert end_time <= mock_obj.mock_now()
    # verify that we did not try to sleep
    # for a really unexpected amount of time
    assert abs(relative_endtime - mock_obj.time_slept) <= epsilon
