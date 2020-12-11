from cr_kyoushi.simulation.util import elements_unique


def test_hashable():
    assert elements_unique([1, 2, 3, 4, 5, 6]) is True
    assert elements_unique([1, 2, 3, 4, 5, 6, 1]) is False


def test_not_hashable():
    class NotHashable:
        pass

    e1 = NotHashable()
    e2 = NotHashable()
    e3 = NotHashable()
    e4 = NotHashable()
    e5 = NotHashable()

    assert elements_unique([e1, e2, e3, e4, e5]) is True
    assert elements_unique([e1, e2, e3, e4, e5, e1]) is False
