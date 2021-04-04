import tempfile

from pathlib import Path

import pytest
import structlog

from cr_kyoushi.simulation.config import (
    FileLogHandler,
    LogFormat,
    LoggingConfig,
    LogHandler,
)
from cr_kyoushi.simulation.logging import (
    LOGGER_NAME,
    configure_logging,
    get_logger,
    rename_event_key_wrapper,
)
from cr_kyoushi.simulation.model import LogLevel


def random_tmp_file():
    return Path(tempfile.gettempdir(), next(tempfile._get_candidate_names()))  # type: ignore


def test_get_logger():
    configure_logging(LoggingConfig())

    assert get_logger().name == LOGGER_NAME


@pytest.mark.parametrize("level", LogLevel.__members__.values())
def test_log_level(level: LogLevel):
    cfg = LoggingConfig()
    cfg.level = level
    log = get_logger()

    configure_logging(cfg)

    assert log.name == LOGGER_NAME
    assert log.level == level


@pytest.mark.parametrize(
    "console, expected_fmt_console, file, expected_fmt_file, handler_count",
    [
        pytest.param(
            LogHandler(
                enabled=True,
                format=LogFormat.PLAIN,
            ),
            structlog.dev.ConsoleRenderer,
            FileLogHandler(
                enabled=True,
                format=LogFormat.PLAIN,
                path=random_tmp_file(),
            ),
            structlog.dev.ConsoleRenderer,
            2,
            id="both-enabled-plain",
        ),
        pytest.param(
            LogHandler(
                enabled=True,
                format=LogFormat.COLORED,
            ),
            structlog.dev.ConsoleRenderer,
            FileLogHandler(
                enabled=False,
                format=LogFormat.PLAIN,
                path=random_tmp_file(),
            ),
            None,
            1,
            id="console-enabled-colored",
        ),
        pytest.param(
            LogHandler(
                enabled=False,
                format=LogFormat.PLAIN,
            ),
            None,
            FileLogHandler(
                enabled=True,
                format=LogFormat.JSON,
                path=random_tmp_file(),
            ),
            # since we wrap the json logger we cannot check it correctly for now
            # so we just check if the result is a function
            type(rename_event_key_wrapper),
            1,
            id="file-enabled-json",
        ),
    ],
)
def test_handler_config(
    console: LogHandler,
    expected_fmt_console,
    file: FileLogHandler,
    expected_fmt_file,
    handler_count: int,
):
    def get_handler(name, handlers):
        for handler in handlers:
            if handler._name == name:
                return handler
        return None

    cfg = LoggingConfig(console=console, file=file)
    log = get_logger()
    configure_logging(cfg)

    handlers = log.handlers

    assert len(handlers) == handler_count

    if console.enabled:
        handler = get_handler("console", handlers)
        assert handler is not None
        assert isinstance(handler.formatter.processor, expected_fmt_console)

        # check console rendere styles
        if console.format == LogFormat.COLORED:
            assert handler.formatter.processor._styles == structlog.dev._ColorfulStyles
        if console.format == LogFormat.PLAIN:
            assert handler.formatter.processor._styles == structlog.dev._PlainStyles

    if file.enabled:
        handler = get_handler("file", handlers)
        assert handler is not None
        assert isinstance(handler.formatter.processor, expected_fmt_file)
        assert handler.baseFilename == str(file.path.absolute())

        # check console rendere styles
        if file.format == LogFormat.COLORED:
            assert handler.formatter.processor._styles == structlog.dev._ColorfulStyles
        if file.format == LogFormat.PLAIN:
            assert handler.formatter.processor._styles == structlog.dev._PlainStyles
