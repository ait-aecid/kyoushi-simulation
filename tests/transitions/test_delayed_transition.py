import time

from cr_kyoushi.simulation import transitions


class NoopDelayedTransition(transitions.DelayedTransition):
    def execute_transition(self, current_state, context):
        return self.target


def test_delayed_transition_init():
    transition = NoopDelayedTransition("test", delay_before=2, delay_after=4)

    assert transition.name == "test"
    assert transition.target is None
    assert transition.delay_before == 2
    assert transition.delay_after == 4


def test_delayed_transition_delay_before():
    precission = 0.01
    expected_wait = 1
    transition = NoopDelayedTransition("test", delay_before=expected_wait)

    # execute and time sleep
    start_seconds = time.time()
    transition.execute("dummy_state", {})
    end_seconds = time.time()

    # calculate waited time
    observed_wait = end_seconds - start_seconds

    assert abs(observed_wait - expected_wait) <= precission


def test_delayed_transition_delay_after():
    precission = 0.01
    expected_wait = 1
    transition = NoopDelayedTransition("test", delay_after=expected_wait)

    # execute and time sleep
    start_seconds = time.time()
    transition.execute("dummy_state", {})
    end_seconds = time.time()

    # calculate waited time
    observed_wait = end_seconds - start_seconds

    assert abs(observed_wait - expected_wait) <= precission


def test_delayed_transition_delay_both():
    precission = 0.01
    expected_wait = 2
    wait = 1
    transition = NoopDelayedTransition("test", delay_before=wait, delay_after=wait)

    # execute and time sleep
    start_seconds = time.time()
    transition.execute("dummy_state", {})
    end_seconds = time.time()

    # calculate waited time
    observed_wait = end_seconds - start_seconds

    assert abs(observed_wait - expected_wait) <= precission
