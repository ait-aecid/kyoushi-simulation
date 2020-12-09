import time

from cr_kyoushi.simulation.util import sleep


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
