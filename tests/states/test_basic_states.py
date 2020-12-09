from cr_kyoushi.simulation import states
from cr_kyoushi.simulation import transitions


class NoneTransition(transitions.Transition):
    def __init__(self, name, target=None, asd=None):
        super().__init__(name, target=target)

    def execute(self, current_state: str, context):
        return self.target


def test_sequential_state_given_transition_returns_it():
    abc = NoneTransition(name="none", target=None)
    seq = states.SequentialState("test", abc)

    # check transition property
    assert len(seq.transitions) == 1
    assert seq.transitions == [abc]

    # check next behaving as expected
    assert seq.next(None) == abc
    assert seq.next({"dummy": "context"}) == abc


def test_final_state_has_no_transition():
    final = states.FinalState("test")

    # check transition property
    assert len(final.transitions) == 0
    assert final.transitions == []

    # check next behaving as expected
    assert final.next(None) is None
    assert final.next({"dummy": "context"}) is None
