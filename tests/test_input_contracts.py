from dataclasses import dataclass
from typing import Any

import pytest

from illustrator_agent import (
    Contract,
    InputValidationError,
    array_contract,
    boolean,
    field,
    finite_number,
    non_empty_string,
    object_contract,
)


@dataclass(frozen=True, slots=True)
class _Metric:
    label: str
    positive: bool


def test_nested_contract_reports_the_exact_input_path() -> None:
    metric = object_contract(
        {"label": non_empty_string(), "positive": boolean()}
    ).map(lambda values: _Metric(**values))
    contract = object_contract({"metrics": array_contract(metric)})

    with pytest.raises(InputValidationError) as caught:
        contract.validate({"metrics": [{"label": "Revenue", "positive": "yes"}]})

    assert caught.value.path == "$.metrics[0].positive"
    assert str(caught.value) == "$.metrics[0].positive: must be a boolean"


def test_default_is_validated_and_domain_object_is_immutable() -> None:
    contract = object_contract(
        {
            "label": non_empty_string(),
            "positive": field(boolean(), default=True),
        }
    ).map(lambda values: _Metric(**values))

    assert contract.validate({"label": "Revenue"}) == _Metric("Revenue", True)


@pytest.mark.parametrize("value", ["metrics", b"metrics", bytearray(b"metrics")])
def test_array_rejects_string_and_byte_sequences(value: object) -> None:
    with pytest.raises(InputValidationError) as caught:
        array_contract(non_empty_string()).validate(value)

    assert caught.value.path == "$"


@pytest.mark.parametrize(
    ("contract", "value"),
    [
        (object_contract({}), []),
        (non_empty_string(), ""),
        (boolean(), 1),
    ],
)
def test_primitive_type_violations_are_value_errors(
    contract: Contract[Any], value: object
) -> None:
    with pytest.raises(ValueError):
        contract.validate(value)


def test_number_rejects_boolean() -> None:
    with pytest.raises(InputValidationError, match=r"^\$: must be a finite number$"):
        finite_number().validate(True)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), 10**400])
def test_number_rejects_non_finite_values(value: int | float) -> None:
    with pytest.raises(InputValidationError, match=r"^\$: must be a finite number$"):
        finite_number().validate(value)


def test_refinement_reports_the_contract_path() -> None:
    contract = object_contract(
        {
            "labels": array_contract(non_empty_string()),
            "values": array_contract(finite_number()),
        }
    ).refine(
        lambda values: len(values["labels"]) == len(values["values"]),
        "labels and values must match",
    )

    with pytest.raises(InputValidationError) as caught:
        object_contract({"chart": contract}).validate(
            {"chart": {"labels": ["Q1"], "values": [1, 2]}}
        )

    assert caught.value.path == "$.chart"
