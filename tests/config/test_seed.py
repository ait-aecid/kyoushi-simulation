import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation import config


@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    # ensure the _SEED is none before each test
    config._SEED = None

    # yield to test execution
    yield


def test_get_seed_when_set(mocker: MockFixture):
    # mock the seed beeing set
    expected_seed = "THIS_IS_THE_SEED"
    mocker.patch("cr_kyoushi.simulation.config._SEED", expected_seed)

    assert config.get_seed() == expected_seed


def test_get_seed_when_not_set(mocker: MockFixture):
    call = mocker.call
    expected_seed = "THIS_IS_THE_SEED"

    # replace configure seed with simply seeding the seed to the expected value
    configure_mock = mocker.Mock()

    def set_seed_patch():
        mocker.patch("cr_kyoushi.simulation.config._SEED", expected_seed)

    configure_mock.side_effect = set_seed_patch
    mocker.patch("cr_kyoushi.simulation.config.configure_seed", configure_mock)

    # assert seed was returned
    assert config.get_seed() == expected_seed
    # assert configure was called with empty seed
    assert configure_mock.mock_calls == [call()]


def test_configure_seed_when_value_given(mocker: MockFixture):
    call = mocker.call
    configure_spy = mocker.spy(config, "configure_seed")

    expected_seed = "THIS_IS_THE_SEED"
    config.configure_seed(expected_seed)

    # assert seed was returned
    assert config.get_seed() == expected_seed
    # assert configure was called only once by us
    assert configure_spy.mock_calls == [call(expected_seed)]


def test_configure_seed_default_value(mocker: MockFixture):
    call = mocker.call
    configure_spy = mocker.spy(config, "configure_seed")
    time_spy = mocker.spy(config.time, "time")

    config.configure_seed()

    # assert seed value is set to current time
    assert config.get_seed() == time_spy.spy_return
    # assert configure was called only once by us
    assert configure_spy.mock_calls == [call()]
