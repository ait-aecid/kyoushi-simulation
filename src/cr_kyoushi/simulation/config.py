import re

from enum import Enum
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Pattern
from typing import Type

from pydantic import BaseModel
from pydantic import BaseSettings
from pydantic import Field
from pydantic import ValidationError
from pydantic import validator
from ruamel.yaml import YAML

from .errors import ConfigValidationError
from .model import LogLevel
from .model import StatemachineConfig


__all__ = [
    "PluginConfig",
    "LoggingConfig",
    "LogFormat",
    "Settings",
    "load_config_file",
    "load_sm_config",
    "load_settings",
]


class PluginConfig(BaseModel):
    """Configuration options for the state machine factory plugin system."""

    include_names: List[Pattern] = Field(
        [re.compile(r".*")],
        description="A list of regular expressions used to define which plugins to include.",
    )
    exclude_names: List[Pattern] = Field(
        [],
        description="A list of regular expressions used to define \
        which plugins to explicitly exclude.",
    )


class LogFormat(str, Enum):
    PLAIN = "plain"
    COLORED = "colored"
    JSON = "json"


class LogHandler(BaseModel):
    enabled: bool = Field(
        False,
        description="If the log handler should be enabled or not",
    )
    format: LogFormat = Field(
        LogFormat.PLAIN,
        description="The log format to use when logging to the console",
    )


class FileLogHandler(LogHandler):
    format: LogFormat = Field(
        LogFormat.JSON,
        description="The log format to use when logging to the console",
    )

    path: Path = Field(
        Path("sm.log"),
        description="The file path to log to, must be set if the handler is enabled.",
    )

    @validator("path")
    def validate_log_path(cls, path: Path) -> Path:
        if path.exists() and not path.is_file():
            raise ValueError(f"Log file path {path.absolute()} is not a file!")
        return path


class LogTimestamp(BaseModel):
    format: Optional[str] = Field(
        None,
        description=(
            r"The strftime string format to use for formating timestamps (e.g., `%Y-%m-%d %H:%M:%S`). "
            "If this is `None` a [UNIX timestamp](https://en.wikipedia.org/wiki/Unix_time) is used."
        ),
    )
    utc: bool = Field(
        True,
        description="If the timestamp should be in UTC or the local timezone.",
    )
    key: str = Field(
        "timestamp",
        description="The key to use for the timestamp.",
    )


class LoggingConfig(BaseSettings):
    """Configuration options for the logging system."""

    level: LogLevel = Field(
        LogLevel.WARNING,
        description="The log level to use for logging",
    )

    timestamp: LogTimestamp = Field(
        LogTimestamp(),
        description="Configuration options for modifying the log timestamps",
    )

    console: LogHandler = Field(
        LogHandler(enabled=True, format=LogFormat.COLORED),
        description="Configuration for the console logger",
    )

    file: FileLogHandler = Field(
        FileLogHandler(enabled=False, format=LogFormat.JSON),
        description="Configuration for the file logger",
    )


class Settings(BaseSettings):
    """Cyber Range Kyoushi Simulation settings"""

    plugin: PluginConfig = Field(
        PluginConfig(),
        description="The plugin system configuration",
    )

    log: LoggingConfig = Field(
        LoggingConfig(),
        description="The logging configuration",
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


def load_settings(
    settings_path: Path,
    log_level: Optional[LogLevel] = None,
) -> Settings:
    try:
        settings_raw = load_config_file(settings_path)
        settings = Settings(
            _env_file=str(object),
            _env_file_encoding=None,
            _secrets_dir=None,
            **settings_raw,
        )

        if log_level is not None:
            settings.log.level = log_level

        return settings
    except ValidationError as val_err:
        raise ConfigValidationError(val_err)
