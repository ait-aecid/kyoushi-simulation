from pathlib import Path

import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation.config import FileLogHandler


def test_file_log_handler_file_validate_raises(mocker: MockFixture):

    path = Path("some_random_path_sdasdj81.log")

    path_mock = mocker.MagicMock(wraps=path)

    # mock file check exists to return True
    path_mock.exists.return_value = True

    # mock is file check to return False
    path_mock.is_file.return_value = False

    with pytest.raises(ValueError):
        FileLogHandler.validate_log_path(path_mock)


@pytest.mark.parametrize(
    "exists, is_file",
    [
        pytest.param(True, True, id="is-file"),
        pytest.param(False, False, id="does-not-exist"),
    ],
)
def test_file_log_handler_file_validate_passes(
    exists: bool,
    is_file: bool,
    mocker: MockFixture,
):

    path = Path("some_random_path_sdasdj81.log")

    path_mock = mocker.MagicMock(wraps=path)

    # mock file check exists to return True
    path_mock.exists.return_value = exists

    # mock is file check to return False
    path_mock.is_file.return_value = is_file

    assert FileLogHandler.validate_log_path(path_mock) == path_mock
