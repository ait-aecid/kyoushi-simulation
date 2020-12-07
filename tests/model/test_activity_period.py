from datetime import datetime

from cr_kyoushi.simulation.model import ActivePeriod
from cr_kyoushi.simulation.model import ComplexActivePeriod
from cr_kyoushi.simulation.model import SimpleActivePeriod
from cr_kyoushi.simulation.model import TimePeriod
from cr_kyoushi.simulation.model import WeekdayActivePeriod


def test_activity_period_parsing():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    weekday_period = WeekdayActivePeriod(week_day="monday", time_period=time_period)

    complex_active_period = ActivePeriod.parse_obj({"week_days": {weekday_period}})
    simple_active_period = ActivePeriod.parse_obj(
        {"week_days": {"monday"}, "time_period": time_period}
    )
    simple_active_no_period = ActivePeriod.parse_obj({"week_days": {"monday"}})

    assert type(complex_active_period.__root__) is ComplexActivePeriod
    assert type(simple_active_period.__root__) is SimpleActivePeriod
    assert type(simple_active_no_period.__root__) is SimpleActivePeriod


def test_complex_weekday_period_parsing():
    source_json = '{"week_days": [{"week_day": "monday"}, {"week_day": "tuesday"}, {"week_day": "monday", "time_period": {"start_time": "00:00", "end_time": "01:00"}}]}'
    source_dict = {
        "week_days": [
            {"week_day": "monday"},
            {"week_day": "tuesday"},
            {
                "week_day": "monday",
                "time_period": {"start_time": "00:00", "end_time": "01:00"},
            },
        ]
    }
    ActivePeriod(__root__=source_dict)
    raw_obj = ActivePeriod.parse_raw(source_json)
    dict_obj = ActivePeriod.parse_obj(source_dict)

    assert len(raw_obj.__root__.week_days) == 2
    assert len(dict_obj.__root__.week_days) == 2


def test_simple_week_days_set_validation():
    source_json = '{"week_days": ["monday", "tuesday", "monday"]}'
    source_dict = {"week_days": ["monday", "tuesday", "monday"]}
    week_days = {0, 1}

    raw_obj = ActivePeriod.parse_raw(source_json)
    dict_obj = ActivePeriod.parse_obj(source_dict)

    assert raw_obj.__root__.week_days == week_days
    assert dict_obj.__root__.week_days == week_days


def test_complex_on_weekday_and_in_period():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    monday_period = WeekdayActivePeriod(week_day="monday", time_period=time_period)
    tuesday_period = WeekdayActivePeriod(week_day="tuesday", time_period=time_period)
    active_period = ActivePeriod.parse_obj(
        {"week_days": {monday_period, tuesday_period}}
    )

    # 2020.11.23 was a monday
    check_datetime = datetime(2020, 11, 23, hour=3, minute=0)
    assert active_period.in_active_period(check_datetime)


def test_complex_on_weekday_no_period():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    monday_period = WeekdayActivePeriod(week_day="monday")
    tuesday_period = WeekdayActivePeriod(week_day="tuesday", time_period=time_period)
    active_period = ActivePeriod.parse_obj(
        {"week_days": {monday_period, tuesday_period}}
    )

    # 2020.11.23 was a monday
    check_datetime = datetime(2020, 11, 23, hour=0, minute=0)
    assert active_period.in_active_period(check_datetime)


def test_complex_not_on_weekday_no_period():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    monday_period = WeekdayActivePeriod(week_day="monday")
    tuesday_period = WeekdayActivePeriod(week_day="tuesday", time_period=time_period)
    active_period = ActivePeriod.parse_obj(
        {"week_days": {monday_period, tuesday_period}}
    )

    # 2020.11.26 was a thursday
    check_datetime = datetime(2020, 11, 26, hour=0, minute=0)
    assert not active_period.in_active_period(check_datetime)


def test_complex_on_weekday_and_not_in_period():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    monday_period = WeekdayActivePeriod(week_day="monday", time_period=time_period)
    tuesday_period = WeekdayActivePeriod(week_day="tuesday", time_period=time_period)
    active_period = ActivePeriod.parse_obj(
        {"week_days": {monday_period, tuesday_period}}
    )

    # 2020.11.23 was a monday
    check_datetime = datetime(2020, 11, 23, hour=0, minute=0)
    assert not active_period.in_active_period(check_datetime)


def test_complex_not_on_weekday():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    monday_period = WeekdayActivePeriod(week_day="monday", time_period=time_period)
    tuesday_period = WeekdayActivePeriod(week_day="tuesday", time_period=time_period)
    active_period = ActivePeriod.parse_obj(
        {"week_days": {monday_period, tuesday_period}}
    )

    # 2020.11.26 was a thursday
    check_datetime = datetime(2020, 11, 26, hour=3, minute=0)
    assert not active_period.in_active_period(check_datetime)


def test_simple_on_weekday_and_in_period():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    week_days = {"monday", "tuesday"}
    active_period = ActivePeriod.parse_obj(
        {"week_days": week_days, "time_period": time_period}
    )

    # 2020.11.23 was a monday
    check_datetime = datetime(2020, 11, 23, hour=3, minute=0)
    assert active_period.in_active_period(check_datetime)


def test_simple_on_weekday_no_period():
    week_days = {"monday", "tuesday"}
    active_period = ActivePeriod.parse_obj({"week_days": week_days})

    # 2020.11.23 was a monday
    check_datetime = datetime(2020, 11, 23, hour=0, minute=0)
    assert active_period.in_active_period(check_datetime)


def test_simple_not_on_weekday_no_period():
    week_days = {"monday", "tuesday"}
    active_period = ActivePeriod.parse_obj({"week_days": week_days})

    # 2020.11.26 was a thursday
    check_datetime = datetime(2020, 11, 26, hour=0, minute=0)
    assert not active_period.in_active_period(check_datetime)


def test_simple_on_weekday_and_not_in_period():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    week_days = {"monday", "tuesday"}
    active_period = ActivePeriod.parse_obj(
        {"week_days": week_days, "time_period": time_period}
    )

    # 2020.11.23 was a monday
    check_datetime = datetime(2020, 11, 23, hour=0, minute=0)
    assert not active_period.in_active_period(check_datetime)


def test_simple_not_on_weekday():
    time_period = TimePeriod(start_time="01:00", end_time="09:00")
    week_days = {"monday", "tuesday"}
    active_period = ActivePeriod.parse_obj(
        {"week_days": week_days, "time_period": time_period}
    )

    # 2020.11.26 was a thursday
    check_datetime = datetime(2020, 11, 26, hour=3, minute=0)
    assert not active_period.in_active_period(check_datetime)
