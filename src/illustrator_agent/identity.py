"""Stable component identities derived from explicit semantic keys."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_SEGMENT = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class IdentityError(ValueError):
    """Base class for identity contract failures."""


class DuplicateSemanticKeyError(IdentityError):
    """A semantic key was repeated in one component scope."""


class StableIdentityCollisionError(IdentityError):
    """Two semantic claims resolved to the same final stable id."""


def validate_identity_segment(segment: str) -> str:
    """Validate one lowercase, delimiter-safe stable identity segment."""

    if not isinstance(segment, str) or not _SEGMENT.fullmatch(segment):
        raise IdentityError(
            "Identity segments must match "
            "'[a-z][a-z0-9]*(?:-[a-z0-9]+)*': "
            f"{segment!r}"
        )
    return segment


@dataclass(frozen=True, slots=True)
class ComponentIdentity:
    """A stable component scope rooted at a semantic key."""

    semantic_key: str
    id: str
    _namespace: IdentityNamespace = field(repr=False, compare=False)

    def claim(self, *segments: str) -> str:
        """Reserve and return a stable descendant id for an emitted item."""

        if not segments:
            raise IdentityError("A component identity claim requires at least one segment")
        validated = tuple(validate_identity_segment(segment) for segment in segments)
        return self._namespace._reserve(
            (*self._namespace.segments, self.semantic_key, *validated),
            owner=f"component {self.semantic_key!r} descendant {validated!r}",
        )


@dataclass(slots=True)
class IdentityNamespace:
    """Allocate deterministic ids and reject ambiguous semantic input early."""

    namespace: str
    segments: tuple[str, ...] = field(init=False)
    _semantic_keys: set[str] = field(default_factory=set, init=False, repr=False)
    _claims: dict[str, str] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, str) or not self.namespace:
            raise IdentityError("Identity namespace must be a non-empty string")
        self.segments = tuple(
            validate_identity_segment(segment) for segment in self.namespace.split(".")
        )

    def _reserve(self, segments: tuple[str, ...], *, owner: str) -> str:
        stable_id = ".".join(segments)
        previous = self._claims.get(stable_id)
        if previous is not None:
            raise StableIdentityCollisionError(
                f"Stable identity collision for {stable_id!r}: {previous} and {owner}"
            )
        self._claims[stable_id] = owner
        return stable_id

    def claim(self, *segments: str) -> str:
        """Reserve a namespace-level id such as a production layer id."""

        if not segments:
            raise IdentityError("An identity claim requires at least one segment")
        validated = tuple(validate_identity_segment(segment) for segment in segments)
        return self._reserve(
            (*self.segments, *validated),
            owner=f"namespace descendant {validated!r}",
        )

    def component(self, semantic_key: str) -> ComponentIdentity:
        """Claim one component key independently of input or render order."""

        validated = validate_identity_segment(semantic_key)
        if validated in self._semantic_keys:
            raise DuplicateSemanticKeyError(
                f"Duplicate semantic key in namespace {self.namespace!r}: {validated!r}"
            )
        self._semantic_keys.add(validated)
        stable_id = self._reserve(
            (*self.segments, validated),
            owner=f"component semantic key {validated!r}",
        )
        return ComponentIdentity(validated, stable_id, self)
