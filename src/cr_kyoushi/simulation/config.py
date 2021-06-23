import random
import re

from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Pattern,
    Type,
)

import numpy as np

from pydantic import (
    BaseModel,
    BaseSettings,
    Field,
    ValidationError,
    validator,
)
from ruamel.yaml import YAML

from .errors import ConfigValidationError
from .model import (
    LogLevel,
    StatemachineConfig,
)


__all__ = [
    "PluginConfig",
    "LoggingConfig",
    "LogFormat",
    "LogHandler",
    "FileLogHandler",
    "Settings",
    "load_config_file",
    "load_sm_config",
    "load_settings",
    "get_seed",
    "configure_seed",
]

_SEED: int


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
    """Enum for log formatter styles"""

    PLAIN = "plain"
    """Human readable structured text format"""

    COLORED = "colored"
    """The same as PLAIN, but colorized"""

    JSON = "json"
    """The log events in JSON format"""


class LogHandler(BaseModel):
    """Configuration for a log handler"""

    enabled: bool = Field(
        False,
        description="If the log handler should be enabled or not",
    )
    format: LogFormat = Field(
        LogFormat.PLAIN,
        description="The log format to use when logging to the console",
    )


class FileLogHandler(LogHandler):
    """Configuration for a file log handler"""

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
        """Validate that the given path is a file if it exists"""
        if path.exists() and not path.is_file():
            raise ValueError(f"Log file path {path.absolute()} is not a file!")
        return path


class LogTimestamp(BaseModel):
    """Configuration for the log timestamp format and key"""

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

    seed: Optional[int] = Field(
        None,
        description="The seed to use for random generators",
    )

    plugin: PluginConfig = Field(
        PluginConfig(),
        description="The plugin system configuration",
    )

    log: LoggingConfig = Field(
        LoggingConfig(),
        description="The logging configuration",
    )


def load_config_file(config_path: Path) -> Dict[Any, Any]:
    """Loads a given a config from the given path and returns a raw dictionary.

    Supported file formats are:
        - YAML

    Args:
        config_path: The file path to read the config from

    Returns:
        The contents of the configuration file converted to a dictionary or `{}`
        if the file is empty or does not exist.
    """
    yaml = YAML(typ="safe")
    if config_path.exists():
        return yaml.load(config_path)
    return {}


def load_sm_config(
    config_path: Path,
    sm_config_type: Type[StatemachineConfig],
) -> StatemachineConfig:
    """Loads and validates the state machine configuration

    Args:
        config_path: The path to load the configuration from
        sm_config_type: The state machine config class to convert to

    Raises:
        ConfigValidationError: If the config validation fails

    Returns:
        The state machine configuration validated and converted
        to the given config class.
    """
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
    seed: Optional[int] = None,
) -> Settings:
    """Loads the Cyber Range Kyoushi Simulation CLI settings

    Args:
        settings_path: The path to load the settings file from
        log_level: The CLI log_level override. This supercedes the config
                   and environment variable values..

    Raises:
        ConfigValidationError: If the config validation fails

    Returns:
        The validated settings object
    """
    try:
        settings_raw = load_config_file(settings_path)

        if log_level is not None:
            settings_raw.setdefault("log", {})["level"] = log_level

        if seed is not None:
            settings_raw["seed"] = seed

        settings = Settings(
            _env_file=str(object),
            _env_file_encoding=None,
            _secrets_dir=None,
            **settings_raw,
        )

        return settings
    except ValidationError as val_err:
        raise ConfigValidationError(val_err)


def configure_seed(seed: Optional[int] = None):
    """Configure a seed for PRNG, if no seed is passed then one is generated.

    Args:
        seed: The seed to use for PRNG
    """
    if seed is None:
        # legacy global numpy requires seeds to be in
        # [0, 2**32-1]
        seed = random.randint(0, 2 ** 32 - 1)
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)


def get_seed() -> int:
    """Get the global random seed value for the simulation library

    Returns:
        The seed value
    """
    # configure seed if not already done
    global _SEED
    if _SEED is None:
        configure_seed()

    # return seed value
    return _SEED
