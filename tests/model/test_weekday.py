import pytest

from pydantic import BaseModel
from pydantic import ValidationError

from cr_kyoushi.simulation.model import Weekday


class WeekdayTestModel(BaseModel):
    weekday: Weekday


def test_parse_from_int_values():
    monday = WeekdayTestModel(weekday=Weekday.MONDAY.value)
    tuesday = WeekdayTestModel(weekday=Weekday.TUESDAY.value)
    wednesday = WeekdayTestModel(weekday=Weekday.WEDNESDAY.value)
    thursday = WeekdayTestModel(weekday=Weekday.THURSDAY.value)
    friday = WeekdayTestModel(weekday=Weekday.FRIDAY.value)
    saturday = WeekdayTestModel(weekday=Weekday.SATURDAY.value)
    sunday = WeekdayTestModel(weekday=Weekday.SUNDAY.value)

    assert monday.weekday == Weekday.MONDAY
    assert tuesday.weekday == Weekday.TUESDAY
    assert wednesday.weekday == Weekday.WEDNESDAY
    assert thursday.weekday == Weekday.THURSDAY
    assert friday.weekday == Weekday.FRIDAY
    assert saturday.weekday == Weekday.SATURDAY
    assert sunday.weekday == Weekday.SUNDAY


def test_parse_from_invalid_int_value():
    with pytest.raises(ValidationError):
        WeekdayTestModel(weekday=10)


def test_parse_from_case_insensitive_string_value():
    monday = WeekdayTestModel(weekday="monDAY")
    tuesday = WeekdayTestModel(weekday="tuesday")
    wednesday = WeekdayTestModel(weekday="WEDNESDAY")
    thursday = WeekdayTestModel(weekday="THURSday")
    friday = WeekdayTestModel(weekday="frIDay")
    saturday = WeekdayTestModel(weekday="SATurDAY")
    sunday = WeekdayTestModel(weekday="sUNDAy")

    assert monday.weekday == Weekday.MONDAY
    assert tuesday.weekday == Weekday.TUESDAY
    assert wednesday.weekday == Weekday.WEDNESDAY
    assert thursday.weekday == Weekday.THURSDAY
    assert friday.weekday == Weekday.FRIDAY
    assert saturday.weekday == Weekday.SATURDAY
    assert sunday.weekday == Weekday.SUNDAY


def test_parse_from_invalid_string_value():
    with pytest.raises(ValidationError):
        WeekdayTestModel(weekday="notaday")


def test_parse_from_enum():
    monday = WeekdayTestModel(weekday=Weekday.MONDAY)
    assert monday.weekday == Weekday.MONDAY
