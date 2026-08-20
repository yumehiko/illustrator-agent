import pytest

from illustrator_agent import (
    DuplicateSemanticKeyError,
    IdentityError,
    IdentityNamespace,
    StableIdentityCollisionError,
)


def _component_ids(keys: tuple[str, ...]) -> dict[str, tuple[str, str]]:
    namespace = IdentityNamespace("campaign")
    return {
        key: (component.id, component.claim("group"))
        for key in keys
        for component in (namespace.component(key),)
    }


def test_semantic_identity_is_independent_of_order_and_unrelated_keys() -> None:
    baseline = _component_ids(("square", "portrait", "banner"))

    assert _component_ids(("banner", "square", "portrait")) == baseline
    extended = _component_ids(("story", "square", "portrait", "banner"))
    assert {key: value for key, value in extended.items() if key != "story"} == baseline
    assert _component_ids(("square", "banner")) == {
        key: baseline[key] for key in ("square", "banner")
    }


def test_identity_rejects_duplicate_semantic_keys_in_one_namespace() -> None:
    namespace = IdentityNamespace("campaign")
    namespace.component("square")

    with pytest.raises(DuplicateSemanticKeyError, match="Duplicate semantic key"):
        namespace.component("square")


@pytest.mark.parametrize(
    ("namespace", "key"),
    [
        ("", "square"),
        ("campaign..variant", "square"),
        ("campaign", ""),
        ("campaign", "Square 1x1"),
        ("campaign", "square.group"),
    ],
)
def test_identity_rejects_invalid_segments(namespace: str, key: str) -> None:
    with pytest.raises(IdentityError, match="namespace|segments"):
        IdentityNamespace(namespace).component(key)


def test_identity_rejects_final_id_collision_across_claim_types() -> None:
    namespace = IdentityNamespace("campaign")
    namespace.claim("square")

    with pytest.raises(StableIdentityCollisionError, match="campaign.square"):
        namespace.component("square")


def test_component_identity_rejects_invalid_descendant_segment() -> None:
    component = IdentityNamespace("campaign").component("square")

    with pytest.raises(IdentityError, match="segments"):
        component.claim("Title")
