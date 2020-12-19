from datetime import datetime
from datetime import time

import pytest

from pydantic import ValidationError

from cr_kyoushi.simulation.model import Weekday
from cr_kyoushi.simulation.model import WorkHours
from cr_kyoushi.simulation.model import WorkSchedule


def test_work_hours_given_start_before_end_then_validation_fails():
    # start_time > end_time
    start_time = time(12, 0, 0)
    end_time = time(9, 0, 9)

    with pytest.raises(ValidationError):
        WorkHours(start_time=start_time, end_time=end_time)


def test_work_hours_given_no_start_validation_does_nothin():
    end_time = time(9, 0, 9)

    result = WorkHours.validate_start_before_end(end_time, {})

    assert end_time == result


@pytest.mark.parametrize(
    "work_day, work_days, expected_result",
    [
        pytest.param(Weekday.FRIDAY, {}, False, id="no-work-days"),
        pytest.param(
            Weekday.SUNDAY,
            {
                Weekday.MONDAY: WorkHours(start_time="12:00", end_time="13:00"),
            },
            False,
            id="not-a-work-day",
        ),
        pytest.param(
            Weekday.MONDAY,
            {
                Weekday.MONDAY: WorkHours(start_time="12:00", end_time="13:00"),
            },
            True,
            id="is-a-work-day",
        ),
    ],
)
def test_is_work_day(work_day, work_days, expected_result):
    schedule = WorkSchedule(work_days=work_days)

    assert schedule.work_days == work_days
    assert schedule.is_work_day(work_day) is expected_result


@pytest.mark.parametrize(
    "check_datetime, work_days, expected_result",
    [
        pytest.param(
            datetime(2020, 12, 18, 12, 0, 0),  # is a friday
            {},
            False,
            id="no-work-days",
        ),
        pytest.param(
            datetime(2020, 12, 18, 12, 0, 0),  # is a friday
            {
                Weekday.MONDAY: WorkHours(start_time="12:00", end_time="13:00"),
            },
            False,
            id="not-a-work-day",
        ),
        pytest.param(
            datetime(2020, 12, 14, 11, 0, 0),  # is a monday
            {
                Weekday.MONDAY: WorkHours(start_time="12:00", end_time="13:00"),
            },
            False,
            id="not-in-work-time",
        ),
        pytest.param(
            datetime(2020, 12, 14, 12, 0, 0),  # is a monday
            {
                Weekday.MONDAY: WorkHours(start_time="12:00", end_time="13:00"),
            },
            True,
            id="in-work-time",
        ),
    ],
)
def test_is_work_time(check_datetime, work_days, expected_result):
    schedule = WorkSchedule(work_days=work_days)

    assert schedule.work_days == work_days
    assert schedule.is_work_time(check_datetime) is expected_result


@pytest.mark.parametrize(
    "check_datetime, work_days, expected_result",
    [
        pytest.param(datetime(2020, 12, 18, 12, 0, 0), {}, None, id="no-work-days"),
        pytest.param(
            datetime(2020, 12, 18, 12, 0, 0),  # is a friday
            {
                Weekday.MONDAY: WorkHours(start_time="12:00", end_time="13:00"),
            },
            datetime(2020, 12, 21, 12, 0, 0),  # the next monday after 2020.12.18
            id="another-day",
        ),
        pytest.param(
            datetime(2020, 12, 18, 10, 0, 0),  # is a friday
            {
                Weekday.FRIDAY: WorkHours(start_time="12:00", end_time="13:00"),
            },
            datetime(2020, 12, 18, 12, 0, 0),
            id="same-day-later",
        ),
        pytest.param(
            datetime(2020, 12, 18, 12, 30, 0),  # is a friday
            {
                Weekday.FRIDAY: WorkHours(start_time="12:00", end_time="13:00"),
            },
            datetime(2020, 12, 18, 12, 0, 0),
            id="currently-working",
        ),
    ],
)
def test_next_work_day(check_datetime, work_days, expected_result):
    schedule = WorkSchedule(work_days=work_days)

    assert schedule.work_days == work_days
    assert schedule.next_work_start(check_datetime) == expected_result
