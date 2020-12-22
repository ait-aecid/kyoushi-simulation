from enum import IntEnum

import pytest

from click.exceptions import BadParameter

from cr_kyoushi.simulation.cli import EnumChoice


class CheckEnum(IntEnum):
    CHOICE_A = 10
    CHOICE_B = 20
    Choice_C = 30


@pytest.mark.parametrize(
    "value, expected_choices, expected_convert, case_sensitive, use_value",
    [
        pytest.param(
            "choiCE_a",
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            CheckEnum.CHOICE_A,
            False,
            False,
            id="case-insensitive-random-case",
        ),
        pytest.param(
            "choice_a",
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            CheckEnum.CHOICE_A,
            False,
            False,
            id="case-insensitive-lower-case",
        ),
        pytest.param(
            "CHOICE_A",
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            CheckEnum.CHOICE_A,
            False,
            False,
            id="case-insensitive-upper-case",
        ),
        pytest.param(
            "CHOICE_A",
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            CheckEnum.CHOICE_A,
            True,
            False,
            id="case-sensitive-upper-case",
        ),
        pytest.param(
            "10",
            ["10", "20", "30"],
            CheckEnum.CHOICE_A,
            False,
            True,
            id="use-value-str",
        ),
        pytest.param(
            CheckEnum.CHOICE_A,
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            CheckEnum.CHOICE_A,
            False,
            False,
            id="convert-enum",
        ),
        pytest.param(
            "Choice_C",
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            CheckEnum.Choice_C,
            False,
            False,
            id="camel-enum-case-insensitive-exact",
        ),
        pytest.param(
            "cHoiCe_C",
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            CheckEnum.Choice_C,
            False,
            False,
            id="camel-enum-case-insensitive",
        ),
        pytest.param(
            "Choice_C",
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            CheckEnum.Choice_C,
            True,
            False,
            id="camel-enum-case-sensitive-exact",
        ),
    ],
)
def test_enum_choice_convert_correctly(
    value,
    expected_choices,
    expected_convert,
    case_sensitive,
    use_value,
):

    choice = EnumChoice(CheckEnum, case_sensitive=case_sensitive, use_value=use_value)

    assert choice.case_sensitive is case_sensitive
    assert choice.use_value is use_value
    assert choice.choices == expected_choices
    assert choice.convert(value) == expected_convert


@pytest.mark.parametrize(
    "value, expected_choices, case_sensitive, use_value",
    [
        pytest.param(
            "choiCE_a",
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            True,
            False,
            id="case-sensitive-incorrect",
        ),
        pytest.param(
            "CHOICE_D",
            ["CHOICE_A", "CHOICE_B", "Choice_C"],
            False,
            False,
            id="case-insensitive-incorrect",
        ),
        pytest.param(
            "40",
            ["10", "20", "30"],
            False,
            True,
            id="use-value-incorrect",
        ),
    ],
)
def test_enum_choice_raises_on_invalid(
    value,
    expected_choices,
    case_sensitive,
    use_value,
):
    choice = EnumChoice(CheckEnum, case_sensitive=case_sensitive, use_value=use_value)

    assert choice.case_sensitive is case_sensitive
    assert choice.use_value is use_value
    assert choice.choices == expected_choices

    with pytest.raises(BadParameter):
        choice.convert(value)
