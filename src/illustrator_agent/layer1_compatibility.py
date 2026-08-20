"""Fail-closed identification of the supported Layer 1 installation."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

LAYER1_DISTRIBUTION = "py-ai-illustrator"
LAYER1_REPOSITORY = "https://github.com/yumehiko/py-ai-illustrator.git"
LAYER1_VERSION = "0.1.0.dev0"
LAYER1_COMMIT = "322b97d2ababc2feb4dd64b6a453885596e74da6"


class Layer1CompatibilityError(RuntimeError):
    """The installed Layer 1 cannot be identified as the supported commit."""


@dataclass(frozen=True, slots=True)
class Layer1Installation:
    """Evidence identifying one installed Layer 1 distribution."""

    version: str
    repository: str
    commit: str
    source: str
    editable: bool
    clean: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalized_repository(value: str) -> str:
    normalized = value.removeprefix("git+").rstrip("/")
    if normalized.startswith("git@github.com:"):
        normalized = "https://github.com/" + normalized.removeprefix("git@github.com:")
    elif normalized.startswith("ssh://git@github.com/"):
        normalized = "https://github.com/" + normalized.removeprefix("ssh://git@github.com/")
    return normalized if normalized.endswith(".git") else f"{normalized}.git"


def _local_path(url: str) -> Path:
    parsed = urlparse(url)
    if parsed.scheme != "file" or (parsed.netloc and parsed.netloc != "localhost"):
        raise Layer1CompatibilityError("editable Layer 1 source must use a local file URL")
    return Path(unquote(parsed.path)).resolve()


def _git(path: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise Layer1CompatibilityError(f"cannot identify editable Layer 1 checkout: {detail}")
    return result.stdout.strip()


def _installation_from_direct_url(version: str, direct_url: dict[str, Any]) -> Layer1Installation:
    source_url = direct_url.get("url")
    if not isinstance(source_url, str) or not source_url:
        raise Layer1CompatibilityError("Layer 1 direct_url.json does not identify its source")

    vcs_info = direct_url.get("vcs_info")
    if isinstance(vcs_info, dict):
        repository = _normalized_repository(source_url)
        commit = vcs_info.get("commit_id")
        if vcs_info.get("vcs") != "git" or not isinstance(commit, str):
            raise Layer1CompatibilityError("Layer 1 VCS source lacks an exact Git commit")
        return Layer1Installation(
            version=version,
            repository=repository,
            commit=commit,
            source="git",
            editable=False,
            clean=True,
        )

    directory_info = direct_url.get("dir_info")
    if not isinstance(directory_info, dict) or directory_info.get("editable") is not True:
        raise Layer1CompatibilityError(
            "Layer 1 must come from the locked Git source or a verified editable checkout"
        )
    path = _local_path(source_url)
    repository = _normalized_repository(_git(path, "remote", "get-url", "origin"))
    commit = _git(path, "rev-parse", "HEAD")
    clean = not _git(path, "status", "--porcelain", "--untracked-files=normal")
    return Layer1Installation(
        version=version,
        repository=repository,
        commit=commit,
        source=str(path),
        editable=True,
        clean=clean,
    )


def inspect_layer1_installation() -> Layer1Installation:
    """Return immutable source evidence for the installed Layer 1 package."""

    try:
        package = distribution(LAYER1_DISTRIBUTION)
    except PackageNotFoundError as error:
        raise Layer1CompatibilityError("py-ai-illustrator is not installed") from error
    raw_direct_url = package.read_text("direct_url.json")
    if raw_direct_url is None:
        raise Layer1CompatibilityError(
            "Layer 1 installation has no direct_url.json and cannot be tied to a commit"
        )
    try:
        direct_url = json.loads(raw_direct_url)
    except json.JSONDecodeError as error:
        raise Layer1CompatibilityError("Layer 1 direct_url.json is invalid") from error
    if not isinstance(direct_url, dict):
        raise Layer1CompatibilityError("Layer 1 direct_url.json must contain an object")
    return _installation_from_direct_url(package.version, direct_url)


def require_layer1_compatibility() -> Layer1Installation:
    """Reject a production gate unless Layer 1 exactly matches the tested source."""

    installation = inspect_layer1_installation()
    mismatches: list[str] = []
    if installation.version != LAYER1_VERSION:
        mismatches.append(f"version {installation.version!r} != {LAYER1_VERSION!r}")
    if _normalized_repository(installation.repository) != LAYER1_REPOSITORY:
        mismatches.append(f"repository {installation.repository!r} != {LAYER1_REPOSITORY!r}")
    if installation.commit != LAYER1_COMMIT:
        mismatches.append(f"commit {installation.commit!r} != {LAYER1_COMMIT!r}")
    if not installation.clean:
        mismatches.append("editable checkout has uncommitted or untracked changes")
    if mismatches:
        raise Layer1CompatibilityError("incompatible Layer 1: " + "; ".join(mismatches))
    return installation
