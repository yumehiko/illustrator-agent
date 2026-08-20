import math

import pytest

from illustrator_agent import fit_linked_image


@pytest.mark.parametrize(
    ("intrinsic", "expected"),
    (
        ((200, 100), (0, 75, 100, 50)),
        ((100, 200), (25, 100, 50, 100)),
        ((100, 100), (0, 100, 100, 100)),
    ),
)
def test_contain_preserves_landscape_portrait_and_square_aspect_ratios(
    intrinsic: tuple[float, float], expected: tuple[float, float, float, float]
) -> None:
    image = fit_linked_image(
        id="photo",
        source="Links/photo.png",
        intrinsic_width=intrinsic[0],
        intrinsic_height=intrinsic[1],
        target_x=0,
        target_top=100,
        target_width=100,
        target_height=100,
        fit_policy="contain",
        horizontal_alignment="center",
        vertical_alignment="center",
    )

    assert (image.x, image.y, image.width, image.height) == pytest.approx(expected)
    assert image.width / image.height == pytest.approx(intrinsic[0] / intrinsic[1])


@pytest.mark.parametrize(
    ("horizontal", "expected_x"),
    (
        ("left", 10),
        ("center", 85),
        ("right", 160),
    ),
)
def test_contain_horizontal_alignment_is_explicit(horizontal: str, expected_x: float) -> None:
    image = fit_linked_image(
        id="photo",
        source="Links/photo.png",
        intrinsic_width=1,
        intrinsic_height=2,
        target_x=10,
        target_top=210,
        target_width=200,
        target_height=100,
        fit_policy="contain",
        horizontal_alignment=horizontal,  # type: ignore[arg-type]
        vertical_alignment="center",
    )

    assert (image.x, image.y, image.width, image.height) == pytest.approx(
        (expected_x, 210, 50, 100)
    )


@pytest.mark.parametrize(
    ("vertical", "expected_y"),
    (("top", 210), ("center", 160), ("bottom", 110)),
)
def test_contain_vertical_alignment_is_explicit(vertical: str, expected_y: float) -> None:
    image = fit_linked_image(
        id="photo",
        source="Links/photo.png",
        intrinsic_width=2,
        intrinsic_height=1,
        target_x=10,
        target_top=210,
        target_width=200,
        target_height=200,
        fit_policy="contain",
        horizontal_alignment="center",
        vertical_alignment=vertical,  # type: ignore[arg-type]
    )

    assert (image.x, image.y, image.width, image.height) == pytest.approx(
        (10, expected_y, 200, 100)
    )


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    (
        ("source", "", "source"),
        ("source", "   ", "source"),
        ("intrinsic_width", 0, "intrinsic_width"),
        ("intrinsic_height", -1, "intrinsic_height"),
        ("target_x", math.inf, "target_x"),
        ("target_top", math.nan, "target_top"),
        ("target_width", 0, "target_width"),
        ("target_height", -1, "target_height"),
    ),
)
def test_image_fit_rejects_invalid_values_before_ir_generation(
    argument: str, value: str | float, message: str
) -> None:
    values: dict[str, object] = {
        "id": "photo",
        "source": "Links/photo.png",
        "intrinsic_width": 320,
        "intrinsic_height": 220,
        "target_x": 0,
        "target_top": 100,
        "target_width": 100,
        "target_height": 100,
        "fit_policy": "contain",
        "horizontal_alignment": "center",
        "vertical_alignment": "center",
    }
    values[argument] = value

    with pytest.raises(ValueError, match=message):
        fit_linked_image(**values)  # type: ignore[arg-type]


def test_image_fit_rejects_unsupported_crop_policy() -> None:
    with pytest.raises(ValueError, match="fit_policy must be 'contain'"):
        fit_linked_image(
            id="photo",
            source="Links/photo.png",
            intrinsic_width=320,
            intrinsic_height=220,
            target_x=0,
            target_top=100,
            target_width=100,
            target_height=100,
            fit_policy="cover",  # type: ignore[arg-type]
            horizontal_alignment="center",
            vertical_alignment="center",
        )
