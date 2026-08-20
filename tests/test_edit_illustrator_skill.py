import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL_ROOT = ROOT / "skills" / "edit-illustrator"
SKILL = SKILL_ROOT / "SKILL.md"
NEW_PRODUCTION = SKILL_ROOT / "references" / "new-production.md"
LOCAL_EDIT = SKILL_ROOT / "references" / "local-ai-edit.md"


def _frontmatter(document: str) -> dict[str, str]:
    opening, body, _remainder = document.split("---", 2)
    assert opening == ""
    return dict(line.split(": ", 1) for line in body.strip().splitlines())


def _local_links(document: Path) -> list[Path]:
    targets = re.findall(r"\[[^]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8"))
    return [
        (document.parent / target.split("#", 1)[0]).resolve()
        for target in targets
        if not target.startswith(("#", "http://", "https://"))
    ]


def _assert_in_order(document: str, values: tuple[str, ...]) -> None:
    positions = [document.index(value) for value in values]
    assert positions == sorted(positions)


def test_skill_has_minimal_routed_structure() -> None:
    files = {
        path.relative_to(SKILL_ROOT).as_posix()
        for path in SKILL_ROOT.rglob("*")
        if path.is_file()
    }

    assert files == {
        "SKILL.md",
        "agents/openai.yaml",
        "references/local-ai-edit.md",
        "references/new-production.md",
    }
    frontmatter = _frontmatter(SKILL.read_text(encoding="utf-8"))
    assert frontmatter["name"] == "edit-illustrator"
    assert "editable Adobe Illustrator file" in frontmatter["description"]
    assert len(SKILL.read_text(encoding="utf-8").splitlines()) < 80


def test_every_repository_reference_resolves() -> None:
    documents = (SKILL, NEW_PRODUCTION, LOCAL_EDIT)
    links = [link for document in documents for link in _local_links(document)]

    assert links
    assert all(link.exists() for link in links)
    assert NEW_PRODUCTION.resolve() in links
    assert LOCAL_EDIT.resolve() in links


def test_new_production_routes_to_all_production_sources() -> None:
    links = set(_local_links(NEW_PRODUCTION))
    required = {
        ROOT / "src" / "illustrator_agent" / "__init__.py",
        ROOT / "src" / "illustrator_agent" / "production_contract.py",
        ROOT / "examples" / "production_runner.py",
        ROOT / "examples" / "quarterly_kpi_report",
        ROOT / "examples" / "japanese_schedule",
        ROOT / "examples" / "product_catalog",
        ROOT / "examples" / "campaign_variants",
    }

    assert {path.resolve() for path in required} <= links


def test_new_production_preserves_gate_boundaries() -> None:
    reference = NEW_PRODUCTION.read_text(encoding="utf-8")

    _assert_in_order(
        reference,
        (
            "verify_reference_document",
            "compile_reference_production",
            "awaiting-visual-acceptance",
            "visual acceptance",
        ),
    )
    assert "ProductionContract" in reference
    assert "build/<production-id>-<revision>" in reference


def test_local_edit_uses_locked_fail_closed_pipeline() -> None:
    reference = LOCAL_EDIT.read_text(encoding="utf-8")

    _assert_in_order(
        reference,
        (
            "py-ai inspect",
            "py-ai plan",
            "py-ai apply",
            "py-ai validate",
            "py-ai diff",
        ),
    )
    assert "source_sha256" in reference
    assert reference.count("uv run --locked py-ai") >= 6
    assert "legacy-ai7-trusted-v1" in reference
    assert "modern-ai-synchronized-patch-v1" in reference
    assert "applicable: true" in reference
    assert "applied: true" in reference


def test_skill_metadata_keeps_automatic_invocation_and_default_prompt() -> None:
    metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert 'default_prompt: "Use $edit-illustrator ' in metadata
    assert "allow_implicit_invocation: true" in metadata
