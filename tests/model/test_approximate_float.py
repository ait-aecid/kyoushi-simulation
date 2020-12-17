import pytest

from pydantic import ValidationError

from cr_kyoushi.simulation.model import ApproximateFloat


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(1.5, id="decimal-point"),
        pytest.param(1, id="integer-float"),
    ],
)
def test_float_convert(value: float):
    af = ApproximateFloat.convert(value)

    assert af.min == value
    assert af.max == value
    assert af.value == value


@pytest.mark.parametrize(
    "min, max",
    [
        pytest.param(1, 10, id="integer-range"),
        pytest.param(1.13, 15.21, id="float-range"),
        pytest.param(-10, -1, id="negative-integer-range"),
        pytest.param(-15.21, -1.13, id="negative-float-range"),
    ],
)
def test_approximate_value(min: float, max: float):
    af = ApproximateFloat(min=min, max=max)

    assert af.min == min
    assert af.max == max

    assert min <= af.value <= max
    assert min <= af.value <= max
    assert min <= af.value <= max
    assert min <= af.value <= max
    assert min <= af.value <= max


def test_approximate_min_max_validation():

    af_ok = ApproximateFloat(min=0, max=2)

    assert af_ok.min == 0
    assert af_ok.max == 2

    with pytest.raises(ValidationError):
        ApproximateFloat(min=2, max=0)
