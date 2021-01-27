import pytest

from cr_kyoushi.simulation.util import (
    calculate_propabilities,
    normalize_propabilities,
)


@pytest.mark.parametrize(
    "p, expected",
    [
        pytest.param(
            [1, 1, 1, 1],
            [0.25, 0.25, 0.25, 0.25],
            id="uniform-scale-down",
        ),
        pytest.param(
            [0.1, 0.1, 0.1, 0.1],
            [0.25, 0.25, 0.25, 0.25],
            id="uniform-scale-up",
        ),
        pytest.param(
            [0.25, 0.5, 0.75, 1],
            [0.1, 0.2, 0.3, 0.4],
            id="rising-scale-down",
        ),
        pytest.param(
            [0.025, 0.05, 0.075, 0.1],
            [0.1, 0.2, 0.3, 0.4],
            id="rising-scale-up",
        ),
        pytest.param(
            [3, 5, 1, 2.5],
            [
                0.2608695652173913043478,
                0.434782608695652173913,
                0.08695652173913043478261,
                0.2173913043478260869565,
            ],
            id="random-scale-down",
        ),
        pytest.param(
            [0.3, 0.5, 0.1, 0.25],
            [
                0.2608695652173913043478,
                0.434782608695652173913,
                0.08695652173913043478261,
                0.2173913043478260869565,
            ],
            id="random-scale-up",
        ),
    ],
)
def test_normalize(p, expected):
    cmp_tolerance = 1e-15
    normalized = normalize_propabilities(p)

    assert abs(1 - sum(normalized)) <= 1e-8
    for i in range(0, len(normalized)):
        assert abs(normalized[i] - expected[i]) < cmp_tolerance


def test_normalize_given_negative_fails():
    p = [0.1, 0.2, 0.3, 0.4, -0.5, 0.6]
    with pytest.raises(ValueError):
        normalize_propabilities(p)


def test_normalize_given_zero_sum_fails():
    p = [0, 0, 0, 0, 0, 0]
    with pytest.raises(ValueError):
        normalize_propabilities(p)


def test_normalize_given_no_check_skips_check():
    # this sums to 1 so it should be returned as is
    # given no negative number check
    p = [0, -1, 1, 1, 0, 0]
    p_result = normalize_propabilities(p, check_positive=False)
    assert p == p_result


@pytest.mark.parametrize(
    "w, m",
    [
        pytest.param(
            [0.25, 0.25, 0.25, 0.25 + 1e-8 + 1e-16],
            [1, 1, 1, 1],
            id="total-bigger",
        ),
        pytest.param(
            [0.25, 0.25, 0.25, 0.25 - 1e-8 - 1e-16],
            [1, 1, 1, 1],
            id="modifiers-zero",
        ),
    ],
)
def test_calculate_propabilities_given_invalid_weights_fails(w, m):
    with pytest.raises(ValueError):
        calculate_propabilities(w, m)


@pytest.mark.parametrize(
    "w, m",
    [
        pytest.param([0, 0, 0, 0], [1, 1, 1, 1], id="weights-zero"),
        pytest.param([0.25, 0.25, 0.25, 0.25], [0, 0, 0, 0], id="modifiers-zero"),
    ],
)
def test_calculate_propabilities_given_all_zero_fails(w, m):
    with pytest.raises(ValueError):
        calculate_propabilities(w, m)


@pytest.mark.parametrize(
    "w, m",
    [
        pytest.param(
            [0.25, -0.25, 0.5, 0.25],
            [1, 1, 1, 1],
            id="weight-negative",
        ),
        pytest.param(
            [0.25, 0.25, 0.25, 0.25],
            [1, -1, 1, 1],
            id="modifier-negative",
        ),
    ],
)
def test_calculate_propabilities_given_negative_fails(w, m):
    with pytest.raises(ValueError):
        calculate_propabilities(w, m)


@pytest.mark.parametrize(
    "w, m",
    [
        pytest.param([0.25, 0.25, 0.25], [1, 1, 1, 1], id="weights-shorter"),
        pytest.param([0.25, 0.25, 0.25, 0.25], [1, 1, 1], id="modifiers-shorter"),
    ],
)
def test_calculate_propabilities_given_len_mismatch_fails(w, m):
    with pytest.raises(ValueError):
        calculate_propabilities(w, m)


@pytest.mark.parametrize(
    "w, m, expected",
    [
        pytest.param(
            [0.25, 0.25, 0.25, 0.25],
            [1, 1, 1, 1],
            [0.25, 0.25, 0.25, 0.25],
            id="unchanged",
        ),
        pytest.param(
            [0.25, 0.25, 0.25, 0.25],
            [4, 4, 4, 4],
            [0.25, 0.25, 0.25, 0.25],
            id="unchanged-same-weights",
        ),
        pytest.param(
            [0.25, 0.25, 0.25, 0.25],
            [0, 0, 0, 1],
            [0, 0, 0, 1],
            id="only-one-active",
        ),
        pytest.param(
            [0.25, 0.25, 0.25, 0.25],
            [3, 1, 1, 1],
            [
                0.5,
                0.1666666666666666666667,
                0.1666666666666666666667,
                0.1666666666666666666667,
            ],
            id="double-one-from-uniform",
        ),
        pytest.param(
            [0.25, 0.25, 0.25, 0.25],
            [243, 243, 1, 1],
            [
                0.5,
                0.5,
                0,
                0,
            ],
            id="double-two-from-uniform",
        ),
    ],
)
def test_calculate_propabilities(w, m, expected):
    cmp_tolerance = 0.01
    p = calculate_propabilities(w, m)
    assert abs(1 - sum(p)) <= 1e-8
    for i in range(0, len(p)):
        assert abs(p[i] - expected[i]) < cmp_tolerance
