import os

from pathlib import Path
from typing import Any
from typing import Dict

import pytest

from cr_kyoushi.simulation import config
from cr_kyoushi.simulation import errors
from cr_kyoushi.simulation import model


FILE_DIR = os.path.dirname(__file__)


@pytest.fixture()
def config_class():
    from pydantic import BaseModel

    class TestConfig(BaseModel):
        str_field: str
        int_field: int

    return TestConfig


def test_given_no_config_return_empty_dicts():
    path = Path(f"{FILE_DIR}/DOES_NOT_EXIST.yml")
    assert path.exists() is False
    cfg = config.load_config_file(path)
    assert cfg == {"plugin": {}, "sm": {}}


def test_given_config_return_correct_dict():
    cfg_expected = {
        "plugin": {"include_names": ["test.*"]},
        "sm": {
            "activity_period": {
                "week_days": ["monday"],
                "time_period": {"start_time": "00:00", "end_time": "01:00"},
            }
        },
    }
    path = Path(f"{FILE_DIR}/test_config_loading.yml")
    assert path.exists()
    cfg = config.load_config_file(path)
    assert cfg_expected == cfg


def test_load_valid_plugin_config():
    plugin_cfg = {"plugin": {"include_names": ["test.*", "cfg.*"]}}
    expected_cfg = model.PluginConfig(include_names=["test.*", "cfg.*"])
    cfg = config.load_plugin_config(plugin_cfg)
    assert expected_cfg == cfg


def test_load_empty_plugin_config():
    plugin_cfg: Dict[str, Any] = {}
    expected_cfg = model.PluginConfig()
    cfg = config.load_plugin_config(plugin_cfg)
    assert expected_cfg == cfg


def test_load_invvalid_plugin_config():
    plugin_cfg = {"plugin": {"include_names": ["test.*", "cfg.*"], "exclude_names": 2}}
    with pytest.raises(errors.ConfigValidationError):
        config.load_plugin_config(plugin_cfg)


def test_load_valid_config(config_class):
    plugin_cfg = {"include_names": ["test.*", "cfg.*"]}
    sm_cfg = {"str_field": "string", "int_field": 0}
    input_cfg = {"plugin": plugin_cfg, "sm": sm_cfg}

    expected_plugin_cfg = model.PluginConfig(include_names=["test.*", "cfg.*"])
    expected_sm_cfg = config_class(str_field="string", int_field=0)

    cfg = config.load_config(input_cfg, config_class)
    assert isinstance(cfg.plugin, model.PluginConfig)
    assert isinstance(cfg.sm, config_class)
    assert expected_plugin_cfg == cfg.plugin
    assert expected_sm_cfg == cfg.sm


def test_load_config_invalid_sm(config_class):
    plugin_cfg = {"include_names": ["test.*", "cfg.*"]}
    sm_cfg = {"str_field": "string", "int_field": "NOT AN INT"}
    input_cfg = {"plugin": plugin_cfg, "sm": sm_cfg}

    with pytest.raises(errors.ConfigValidationError):
        config.load_config(input_cfg, config_class)


def test_load_config_invalid_plugin(config_class):
    plugin_cfg = {"include_names": "NOT A LIST"}
    sm_cfg = {"str_field": "string", "int_field": 0}
    input_cfg = {"plugin": plugin_cfg, "sm": sm_cfg}

    with pytest.raises(errors.ConfigValidationError):
        config.load_config(input_cfg, config_class)
