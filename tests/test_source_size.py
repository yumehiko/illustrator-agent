from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE_ROOTS = (ROOT / "src", ROOT / "examples")
SPLIT_REQUIRED_LINES = 800
ABSOLUTE_MAX_LINES = 1000

# A path may appear here only with a short reason why immediate splitting would
# make the responsibility boundary worse. Files above ABSOLUTE_MAX_LINES cannot
# be excepted.
LINE_COUNT_EXCEPTIONS: dict[str, str] = {}


def test_python_sources_do_not_silently_grow_past_split_thresholds() -> None:
    counts = {
        path.relative_to(ROOT).as_posix(): len(path.read_text(encoding="utf-8").splitlines())
        for source_root in SOURCE_ROOTS
        for path in source_root.rglob("*.py")
    }

    over_absolute = {path: count for path, count in counts.items() if count > ABSOLUTE_MAX_LINES}
    over_review = {
        path: count
        for path, count in counts.items()
        if count > SPLIT_REQUIRED_LINES and path not in LINE_COUNT_EXCEPTIONS
    }

    assert not over_absolute, f"Python source exceeds {ABSOLUTE_MAX_LINES} lines: {over_absolute}"
    assert not over_review, (
        f"Python source exceeds {SPLIT_REQUIRED_LINES} lines without an explicit exception: "
        f"{over_review}"
    )
