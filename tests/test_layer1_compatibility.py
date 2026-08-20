import inspect
import json
import tomllib
from pathlib import Path
from types import SimpleNamespace

import py_ai_illustrator
import pytest
from py_ai_illustrator import (
    Artboard,
    CmykColor,
    Color,
    ControlPoint,
    Document,
    Group,
    Layer,
    LayerItemRef,
    LinkedImage,
    Point,
    TextFrame,
    compile_native_ai,
    iter_linked_images,
    package_linked_images,
    render_preview,
    semantic_diff,
)
from py_ai_illustrator import (
    Path as IllustratorPath,
)
from py_ai_illustrator.illustrator import list_illustrator_fonts, run_illustrator_test
from py_ai_illustrator.model import ProcessColor

from illustrator_agent import layer1_compatibility
from illustrator_agent.layer1_compatibility import (
    LAYER1_COMMIT,
    LAYER1_REPOSITORY,
    LAYER1_VERSION,
    Layer1CompatibilityError,
    require_layer1_compatibility,
)

ROOT = Path(__file__).resolve().parents[1]


def _distribution(*, version: str = LAYER1_VERSION, direct_url: object) -> SimpleNamespace:
    return SimpleNamespace(
        version=version,
        read_text=lambda name: json.dumps(direct_url) if name == "direct_url.json" else None,
    )


def test_locked_source_matches_the_runtime_compatibility_boundary() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    source = project["tool"]["uv"]["sources"]["py-ai-illustrator"]
    assert source == {"git": LAYER1_REPOSITORY, "rev": LAYER1_COMMIT}
    assert project["project"]["dependencies"] == [f"py-ai-illustrator>={LAYER1_VERSION}"]

    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    package = next(item for item in lock["package"] if item["name"] == "py-ai-illustrator")
    assert package["version"] == LAYER1_VERSION
    assert package["source"]["git"].endswith(f"?rev={LAYER1_COMMIT}#{LAYER1_COMMIT}")


def test_used_layer1_public_api_remains_available() -> None:
    public_types = (
        Artboard,
        Color,
        ControlPoint,
        Document,
        Group,
        Layer,
        LayerItemRef,
        LinkedImage,
        IllustratorPath,
        Point,
        TextFrame,
    )
    assert all(not value.__name__.startswith("_") for value in public_types)
    assert {
        *(value.__name__ for value in public_types),
        "CmykColor",
        "compile_native_ai",
        "iter_linked_images",
        "package_linked_images",
        "render_preview",
        "semantic_diff",
    } <= set(py_ai_illustrator.__all__)
    assert ProcessColor == Color | CmykColor
    assert set(inspect.signature(compile_native_ai).parameters) >= {
        "source",
        "destination",
        "source_base",
        "timeout",
    }
    assert set(inspect.signature(render_preview).parameters) >= {"source", "output", "timeout"}
    assert set(inspect.signature(list_illustrator_fonts).parameters) >= {
        "query",
        "required",
        "timeout",
    }
    assert set(inspect.signature(run_illustrator_test).parameters) >= {"source", "timeout"}
    assert callable(iter_linked_images)
    assert callable(package_linked_images)
    assert callable(semantic_diff)


def test_locked_git_installation_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        layer1_compatibility,
        "distribution",
        lambda _: _distribution(
            direct_url={
                "url": LAYER1_REPOSITORY,
                "vcs_info": {"vcs": "git", "commit_id": LAYER1_COMMIT},
            }
        ),
    )

    installation = require_layer1_compatibility()

    assert installation.commit == LAYER1_COMMIT
    assert installation.source == "git"
    assert installation.clean is True


def test_matching_ssh_origin_is_accepted_for_an_editable_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        layer1_compatibility,
        "distribution",
        lambda _: _distribution(
            direct_url={
                "url": "file:///work/py-ai-illustrator",
                "dir_info": {"editable": True},
            }
        ),
    )
    responses = iter(["git@github.com:yumehiko/py-ai-illustrator.git", LAYER1_COMMIT, ""])
    monkeypatch.setattr(layer1_compatibility, "_git", lambda *_: next(responses))

    installation = require_layer1_compatibility()

    assert installation.editable is True
    assert installation.clean is True


def test_wrong_git_commit_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        layer1_compatibility,
        "distribution",
        lambda _: _distribution(
            direct_url={
                "url": LAYER1_REPOSITORY,
                "vcs_info": {"vcs": "git", "commit_id": "0" * 40},
            }
        ),
    )

    with pytest.raises(Layer1CompatibilityError, match="commit"):
        require_layer1_compatibility()


def test_dirty_editable_checkout_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        layer1_compatibility,
        "distribution",
        lambda _: _distribution(
            direct_url={
                "url": "file:///work/py-ai-illustrator",
                "dir_info": {"editable": True},
            }
        ),
    )
    responses = iter([LAYER1_REPOSITORY, LAYER1_COMMIT, " M src/py_ai_illustrator/model.py"])
    monkeypatch.setattr(layer1_compatibility, "_git", lambda *_: next(responses))

    with pytest.raises(Layer1CompatibilityError, match="uncommitted"):
        require_layer1_compatibility()


def test_unidentified_registry_installation_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        layer1_compatibility,
        "distribution",
        lambda _: SimpleNamespace(version=LAYER1_VERSION, read_text=lambda _: None),
    )

    with pytest.raises(Layer1CompatibilityError, match="direct_url.json"):
        require_layer1_compatibility()
