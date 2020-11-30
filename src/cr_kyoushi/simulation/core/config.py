from pathlib import Path
from typing import Any
from typing import Dict

from pydantic import ValidationError
from ruamel.yaml import YAML

from .errors import ConfigValidationError
from .model import Config
from .model import PluginConfig


def load_config_file(config_path: Path) -> Dict[str, Any]:
    yaml = YAML(typ="safe")
    if config_path.exists():
        return yaml.load(config_path)
    return {}


def load_config(config_raw: Dict[str, Any], sm_config_type) -> Config:
    try:
        return Config[sm_config_type].parse_obj(config_raw)  # type: ignore
    except ValidationError as val_err:
        raise ConfigValidationError(val_err)


def load_plugin_config(
    config_raw: Dict[str, Any],
) -> PluginConfig:
    try:
        plugin_config = config_raw.get("plugin", {})
        return PluginConfig.parse_obj(plugin_config)
    except ValidationError as val_err:
        raise ConfigValidationError(val_err)
