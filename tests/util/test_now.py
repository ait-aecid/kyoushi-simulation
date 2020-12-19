from datetime import datetime

from pytest_mock import MockFixture

from cr_kyoushi.simulation.util import now


def test_now_returns_current_time(mocker: MockFixture):
    current_time = datetime(2020, 12, 19, 12, 0)
    # mock the datetime object in util
    now_spy = mocker.patch(
        "cr_kyoushi.simulation.util.datetime", mocker.MagicMock(return_value=...)
    )
    now_spy.now.return_value = current_time

    # verify that util now returns datetime now
    assert now() == current_time
    assert now_spy.mock_calls == [mocker.call.now(None)]
