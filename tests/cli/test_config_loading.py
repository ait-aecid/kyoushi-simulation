import os

from pathlib import Path

import pytest

from pydantic import BaseModel

from cr_kyoushi.simulation import config
from cr_kyoushi.simulation import errors
from cr_kyoushi.simulation import model


FILE_DIR = os.path.dirname(__file__) + "/files"


class SimpleConfig(BaseModel):
    str_field: str
    int_field: int


class ComplexConfig(BaseModel):
    work_schedule: model.WorkSchedule


@pytest.mark.parametrize(
    "config_path, path_exists, expected_dict",
    [
        pytest.param(
            Path(f"{FILE_DIR}/config.yml"),
            True,
            {"plugin": {"include_names": ["test.*", "cfg.*"]}},
            id="settings",
        ),
        pytest.param(
            Path(f"{FILE_DIR}/complex-sm.yml"),
            True,
            {
                "work_schedule": {
                    "work_days": {
                        "monday": {
                            "start_time": "00:00",
                            "end_time": "12:00",
                        }
                    }
                }
            },
            id="complex-sm",
        ),
        pytest.param(
            Path(f"{FILE_DIR}/simple-sm.yml"),
            True,
            {"str_field": "string", "int_field": 0},
            id="simple-sm",
        ),
        pytest.param(
            Path(f"{FILE_DIR}/DOES_NOT_EXIST.yml"),
            False,
            {},
            id="non-existent-file",
        ),
    ],
)
def test_given_config_return_correct_dict(config_path, path_exists, expected_dict):
    assert config_path.exists() is path_exists
    cfg = config.load_config_file(config_path)
    assert expected_dict == cfg


@pytest.mark.parametrize(
    "config_path, path_exists, expected_settings",
    [
        pytest.param(
            Path(f"{FILE_DIR}/config.yml"),
            True,
            config.Settings(
                plugin=model.PluginConfig(include_names=["test.*", "cfg.*"])
            ),
            id="config-file",
        ),
        pytest.param(
            Path(f"{FILE_DIR}/DOES_NOT_EXIST.yml"),
            False,
            config.Settings(),
            id="default",
        ),
    ],
)
def test_load_valid_settings(config_path, path_exists, expected_settings):
    settings = config.load_settings(config_path)

    assert config_path.exists() is path_exists
    assert isinstance(settings, config.Settings)
    assert expected_settings == settings


def test_load_empty_config_file():
    non_existent_path = Path(f"{FILE_DIR}/DOES_NOT_EXIST.yml")
    cfg = config.load_config_file(non_existent_path)
    assert cfg == {}


@pytest.mark.parametrize(
    "config_path",
    [
        pytest.param(
            Path(f"{FILE_DIR}/invalid_plugin_exclude_names.yml"),
            id="exclude-names",
        ),
        pytest.param(
            Path(f"{FILE_DIR}/invalid_plugin_include_names.yml"),
            id="exclude-names",
        ),
    ],
)
def test_load_invalid_settings(config_path):
    with pytest.raises(errors.ConfigValidationError):
        config.load_settings(config_path)


@pytest.mark.parametrize(
    "sm_config_path, config_class, expected_sm_config",
    [
        pytest.param(
            Path(f"{FILE_DIR}/simple-sm.yml"),
            SimpleConfig,
            SimpleConfig(str_field="string", int_field=0),
            id="simple-sm",
        ),
        pytest.param(
            Path(f"{FILE_DIR}/simple-sm.yml"),
            dict,
            {"str_field": "string", "int_field": 0},
            id="simple-dict-cfg",
        ),
        pytest.param(
            Path(f"{FILE_DIR}/complex-sm.yml"),
            ComplexConfig,
            ComplexConfig(
                work_schedule=model.WorkSchedule(
                    work_days={
                        model.Weekday.MONDAY: model.WorkHours(
                            start_time="00:00",
                            end_time="12:00",
                        )
                    }
                )
            ),
            id="complex-sm",
        ),
    ],
)
def test_load_valid_sm_config(sm_config_path, config_class, expected_sm_config):
    cfg = config.load_sm_config(sm_config_path, config_class)
    assert isinstance(cfg, config_class)
    assert expected_sm_config == cfg


def test_load_invalid_sm_config():
    sm_config_path = Path(f"{FILE_DIR}/invalid_sm.yml")
    with pytest.raises(errors.ConfigValidationError):
        config.load_sm_config(sm_config_path, SimpleConfig)
