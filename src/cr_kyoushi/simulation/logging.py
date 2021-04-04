import json
import logging
import logging.config
import re

from functools import partial
from typing import (
    Any,
    Callable,
    List,
    Mapping,
    MutableMapping,
    Tuple,
    Union,
)

import structlog

from pydantic.json import custom_pydantic_encoder

from .config import (
    LogFormat,
    LoggingConfig,
)


JSON_ENCODERS = {
    re.Pattern: lambda p: p.pattern,
}


encoder = partial(custom_pydantic_encoder, JSON_ENCODERS)
"""
Custom encoder based on the pydantic encoder with additional types enabled.
(see `JSON_ENCODERS`)

!!! Note
    This is necessary since the Pydantic JSON encoder
    cannot handle `Pattern` fields as of v1.7.3. The code exists already on
    the master branch and should be part of the next release.
"""


LOGGER_NAME = "cr_kyoushi.simulation"
"""The name of the Cyber Range Kyoushi Simulation logger"""


def rename_event_key(
    logger: logging.Logger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
    field_name: str,
) -> MutableMapping[str, Any]:
    """Processor for renaming the event key to message.

    We do this since this is more compatible with the ecs schema.
    """
    event_dict[field_name] = event_dict.pop("event")
    return event_dict


def rename_event_key_wrapper(
    func: Callable[[logging.Logger, str, MutableMapping[str, Any]], Any],
    field_name: str = "message",
) -> Callable[
    [logging.Logger, str, MutableMapping[str, Any]], MutableMapping[str, Any]
]:
    """Processor wrapper that renames the event field before calling the given processor.

    Args:
        func: The processor to be wrapped
        field_name: The field name to use instead of `event`

    Returns:
        The wrapped processor
    """

    def _rename_event_key(
        logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        event_dict = rename_event_key(logger, method_name, event_dict, field_name)
        return func(logger, method_name, event_dict)

    return _rename_event_key


def get_logger() -> structlog.stdlib.BoundLogger:
    """Convenience function for getting the Cyber Range Kyoushi Simulation logger."""
    return structlog.stdlib.get_logger(LOGGER_NAME)


def configure_logging(logging_config: LoggingConfig):
    """Configures the logging system based on the passed
    [`LoggingConfig`][cr_kyoushi.simulation.config.LoggingConfig]

    Args:
        logging_config: The logging configuration object
    """
    # ensure we start from default config
    structlog.reset_defaults()

    timestamper = structlog.processors.TimeStamper(
        fmt=logging_config.timestamp.format,
        utc=logging_config.timestamp.utc,
        key=logging_config.timestamp.key,
    )
    # shared processors for standard lib and structlog
    shared_processors: List[
        Callable[
            [Any, str, MutableMapping[str, Any]],
            Union[Mapping[str, Any], str, bytes, Tuple[Any, ...]],
        ]
    ] = [
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # processor only for structlog
    processors: List[
        Callable[
            [Any, str, MutableMapping[str, Any]],
            Union[Mapping[str, Any], str, bytes, Tuple[Any, ...]],
        ]
    ] = [structlog.stdlib.filter_by_level]
    processors.extend(shared_processors)
    # the processor formatter wrapper must be last as it changes the
    processors.append(structlog.stdlib.ProcessorFormatter.wrap_for_formatter)

    handlers = {}
    # configure console logging
    if logging_config.console.enabled:
        handlers["console"] = {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": logging_config.console.format,
        }

    # configure file logging
    if logging_config.file.enabled:
        handlers["file"] = {
            "level": "DEBUG",
            "class": "logging.handlers.WatchedFileHandler",
            "filename": str(logging_config.file.path.absolute()),
            "formatter": logging_config.file.format,
        }

    # configure standard lib logging
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                LogFormat.PLAIN: {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=False),
                    "foreign_pre_chain": shared_processors,
                },
                LogFormat.COLORED: {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=True),
                    "foreign_pre_chain": shared_processors,
                },
                LogFormat.JSON: {
                    "()": structlog.stdlib.ProcessorFormatter,
                    # when logging to json we rename the "event" field to "message"
                    "processor": rename_event_key_wrapper(
                        structlog.processors.JSONRenderer(
                            serializer=json.dumps,
                            sort_keys=True,
                            default=encoder,
                        )
                    ),
                    "foreign_pre_chain": shared_processors,
                },
            },
            "handlers": handlers,
            "loggers": {LOGGER_NAME: {"handlers": handlers.keys(), "propagate": True}},
        }
    )

    # apply structlog config
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # set the log level
    logger = structlog.get_logger(LOGGER_NAME)
    logger.setLevel(logging_config.level)
