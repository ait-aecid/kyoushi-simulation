from pathlib import Path
from typing import Any
from typing import Dict
from typing import Type

from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import Field
from pydantic import ValidationError
from ruamel.yaml import YAML

from .errors import ConfigValidationError
from .model import PluginConfig
from .model import StatemachineConfig


__all__ = ["Settings", "load_config_file", "load_sm_config", "load_settings"]


class Settings(BaseSettings):
    """Cyber Range Kyoushi Simulation settings"""

    plugin: PluginConfig = Field(
        PluginConfig(), description="The plugin system configuration"
    )


def load_config_file(config_path: Path) -> Dict[Any, Any]:
    yaml = YAML(typ="safe")
    if config_path.exists():
        return yaml.load(config_path)
    return {}


def load_sm_config(
    config_path: Path,
    sm_config_type: Type[StatemachineConfig],
) -> StatemachineConfig:
    try:
        config_raw = load_config_file(config_path)
        if issubclass(sm_config_type, BaseModel):
            return sm_config_type.parse_obj(config_raw)
        else:
            return config_raw

    except ValidationError as val_err:
        raise ConfigValidationError(val_err)


def load_settings(settings_path: Path, **kwargs) -> Settings:
    try:
        settings_raw = load_config_file(settings_path)
        settings_raw.update(kwargs)
        return Settings(**settings_raw)
    except ValidationError as val_err:
        raise ConfigValidationError(val_err)
