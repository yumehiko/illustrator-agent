from pathlib import Path

import pytest

from examples import BUILD_ROOT, production_runner
from examples.campaign_variants import cli as campaign_cli
from examples.generate_product_swatch import DEFAULT_OUTPUT as SWATCH_OUTPUT
from examples.generate_product_swatch import main as generate_swatch
from examples.japanese_schedule import cli as schedule_cli
from examples.product_catalog import cli as catalog_cli
from examples.quarterly_kpi_report import cli as report_cli

ROOT = Path(__file__).parents[1]
PRODUCTION_MODULES = (report_cli, schedule_cli, catalog_cli, campaign_cli)


def test_example_inventory_contains_only_classified_entry_points() -> None:
    root_modules = {path.name for path in (ROOT / "examples").glob("*.py")}
    production_packages = {
        path.parent.name for path in (ROOT / "examples").glob("*/__main__.py")
    }

    assert root_modules == {
        "__init__.py",
        "generate_product_swatch.py",
        "production_runner.py",
    }
    assert production_packages == {
        "campaign_variants",
        "japanese_schedule",
        "product_catalog",
        "quarterly_kpi_report",
    }


def test_all_default_generated_outputs_are_under_build() -> None:
    outputs = [*(module.DEFAULT_OUTPUT for module in PRODUCTION_MODULES), SWATCH_OUTPUT]

    assert all(output.resolve().is_relative_to(BUILD_ROOT.resolve()) for output in outputs)


def test_all_production_clis_use_the_shared_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def fake_compile(build_document, **arguments):
        calls.append((build_document, arguments))
        return {
            "status": "awaiting-visual-acceptance",
            "report_path": str(arguments["output_directory"] / "report.json"),
        }

    monkeypatch.setattr(production_runner, "compile_reference_production", fake_compile)

    assert [module.main([]) for module in PRODUCTION_MODULES] == [0, 0, 0, 0]
    assert [call[1]["contract"].production_id for call in calls] == [
        "quarterly-kpi-report",
        "japanese-schedule",
        "product-catalog",
        "campaign-variants",
    ]
    assert all(call[1]["output_directory"].is_relative_to(BUILD_ROOT) for call in calls)


def test_shared_runner_forwards_options_and_failed_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}
    output_directory = BUILD_ROOT / "test-options"

    def fake_compile(build_document, **arguments):
        captured.update(arguments)
        return {
            "status": "failed",
            "report_path": str(output_directory / "report.json"),
        }

    monkeypatch.setattr(production_runner, "compile_reference_production", fake_compile)

    result = catalog_cli.main(
        [
            "--output-dir",
            str(output_directory),
            "--force",
            "--accept-visual-by",
            "Reviewer",
            "--timeout",
            "45",
        ]
    )

    assert result == 1
    assert captured["output_directory"] == output_directory
    assert captured["force"] is True
    assert captured["visual_accepted_by"] == "Reviewer"
    assert captured["timeout"] == 45.0


def test_minimal_fixture_recipe_rejects_output_outside_build(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="fixture output must be under"):
        generate_swatch(["--output", str(tmp_path / "product-swatch.png")])


def test_production_runner_rejects_output_outside_build(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="production output must be under"):
        catalog_cli.main(["--output-dir", str(tmp_path)])
