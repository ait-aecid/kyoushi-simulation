import pytest

from pydantic import BaseModel
from pydantic import ValidationError

from cr_kyoushi.simulation.model import LogLevel


class LogLevelTestModel(BaseModel):
    log_level: LogLevel


def test_parse_from_int_values():
    notset = LogLevelTestModel(log_level=LogLevel.NOTSET.value)
    debug = LogLevelTestModel(log_level=LogLevel.DEBUG.value)
    info = LogLevelTestModel(log_level=LogLevel.INFO.value)
    warning = LogLevelTestModel(log_level=LogLevel.WARNING.value)
    error = LogLevelTestModel(log_level=LogLevel.ERROR.value)
    critical = LogLevelTestModel(log_level=LogLevel.CRITICAL.value)

    assert notset.log_level == LogLevel.NOTSET
    assert debug.log_level == LogLevel.DEBUG
    assert info.log_level == LogLevel.INFO
    assert warning.log_level == LogLevel.WARNING
    assert error.log_level == LogLevel.ERROR
    assert critical.log_level == LogLevel.CRITICAL


def test_parse_from_invalid_int_value():
    with pytest.raises(ValidationError):
        LogLevelTestModel(log_level=1337)


def test_parse_from_case_insensitive_string_value():
    notset = LogLevelTestModel(log_level="noTset")
    debug = LogLevelTestModel(log_level="debug")
    info = LogLevelTestModel(log_level="INFO")
    warning = LogLevelTestModel(log_level="WARNing")
    error = LogLevelTestModel(log_level="eRRor")
    critical = LogLevelTestModel(log_level="CriTIcaL")

    assert notset.log_level == LogLevel.NOTSET
    assert debug.log_level == LogLevel.DEBUG
    assert info.log_level == LogLevel.INFO
    assert warning.log_level == LogLevel.WARNING
    assert error.log_level == LogLevel.ERROR
    assert critical.log_level == LogLevel.CRITICAL


def test_parse_from_invalid_string_value():
    with pytest.raises(ValidationError):
        LogLevelTestModel(log_level="notaloglevel")


def test_parse_from_enum():
    notset = LogLevelTestModel(log_level=LogLevel.NOTSET)
    assert notset.log_level == LogLevel.NOTSET
