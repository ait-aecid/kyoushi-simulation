import json
import logging
import logging.config

import structlog

from pydantic.json import pydantic_encoder

from .config import LogFormat
from .config import LoggingConfig


LOGGER_NAME = "cr_kyoushi.simulation"


def get_logger() -> structlog.BoundLogger:
    return structlog.get_logger(LOGGER_NAME)


def configure_logging(logging_config: LoggingConfig):
    # ensure we start from default config
    structlog.reset_defaults()

    timestamper = structlog.processors.TimeStamper(
        fmt=logging_config.timestamp.format,
        utc=logging_config.timestamp.utc,
        key=logging_config.timestamp.key,
    )
    # shared processors for standard lib and structlog
    shared_processors = [
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # processor only for structlog
    processors = [structlog.stdlib.filter_by_level]
    processors.extend(shared_processors)
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
                    "processor": structlog.processors.JSONRenderer(
                        serializer=json.dumps,
                        sort_keys=True,
                        default=pydantic_encoder,
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
