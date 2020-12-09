import sys

from signal import SIGINT
from signal import getsignal

import pytest

from pytest_mock import MockFixture

from cr_kyoushi.simulation.util import SkipSectionError
from cr_kyoushi.simulation.util import skip_on_interrupt
from cr_kyoushi.simulation.util import skip_on_interrupt_sig_handler


def __call_sig_handler(handler):
    # raise an exception so we can get a frame
    try:
        raise TypeError
    except TypeError:
        tb = sys.exc_info()[2]
        if tb is not None:
            tb.tb_frame
            handler(SIGINT, tb.tb_frame)
        else:
            raise Exception()


def test_signal_handler():
    with pytest.raises(SkipSectionError):
        skip_on_interrupt_sig_handler(SIGINT, None)


def test_skip_on_interrupt_restores_handler(mocker: MockFixture):
    reachable = mocker.stub(name="reachable")

    original_handler = getsignal(SIGINT)
    skip_handler = None
    with skip_on_interrupt():
        skip_handler = getsignal(SIGINT)
        reachable()

    restored_handler = getsignal(SIGINT)

    # verify skip handler was correctly set
    assert skip_handler is not None
    assert skip_handler != original_handler

    # verify original handler was correctly restored
    assert restored_handler == original_handler

    # verify the inner function was reached
    reachable.assert_called_once()


def test_skip_on_interrupt_double_signal_calls_original_handler(mocker: MockFixture):
    unreachable = mocker.stub(name="unreachable")

    # patch the sleep function in skip on interrupt
    # to simulate a SIGINT instead
    sleep_patch = mocker.patch("cr_kyoushi.simulation.util.time.sleep")
    sleep_patch.side_effect = lambda x: __call_sig_handler(getsignal(SIGINT))

    with pytest.raises(KeyboardInterrupt):
        with skip_on_interrupt():
            # simulate CTRL+C by calling signal handler directly
            __call_sig_handler(getsignal(SIGINT))
            unreachable()

    unreachable.assert_not_called()


def test_skip_on_interrupt_skips(mocker: MockFixture):
    unreachable = mocker.stub(name="unreachable")

    with skip_on_interrupt():
        # simulate CTRL+C by calling signal handler directly
        __call_sig_handler(getsignal(SIGINT))
        unreachable()

    unreachable.assert_not_called()
