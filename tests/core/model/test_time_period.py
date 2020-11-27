from datetime import time

from cr_kyoushi.simulation.core.model import TimePeriod


def test_time_period_in_period_start_le_end():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    check_time = time(3, 0, 0)
    assert time_period.in_period(check_time)


def test_time_period_not_in_period_start_le_end():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    check_time_before = time(0, 0, 0)
    check_time_after = time(10, 0, 0)

    assert not time_period.in_period(check_time_before)
    assert not time_period.in_period(check_time_after)


def test_time_period_in_period_start_ge_end():
    time_period = TimePeriod(start_time="09:00", end_time="01:00")
    check_time_day1 = time(10, 0, 0)
    check_time_day2 = time(0, 0, 0)
    assert time_period.in_period(check_time_day1)
    assert time_period.in_period(check_time_day2)


def test_time_period_not_in_period_start_ge_end():
    time_period = TimePeriod(start_time="09:00", end_time="01:00")
    check_time_before = time(8, 0, 0)
    check_time_after = time(2, 0, 0)

    assert not time_period.in_period(check_time_before)
    assert not time_period.in_period(check_time_after)
