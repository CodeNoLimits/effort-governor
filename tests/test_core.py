"""Tests for effort_governor.core — run: python3 -m pytest -q  (or: python3 tests/test_core.py)."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from effort_governor.core import classify, directive, badge, ICON  # noqa: E402

CASES = [
    ("thanks, that's all",                 "LOW"),
    ("show me the git status",             "LOW"),
    ("rename the variable foo to bar",     "LOW"),
    ("add a share button to the page",     "MEDIUM"),
    ("optimize the database query",        "HIGH"),
    ("why does the build crash, debug it", "MAX"),   # 3+ signals -> MAX (upward bias)
    ("refactor the whole architecture from scratch", "MAX"),
    ("x" * 700,                            "MAX"),   # long -> MAX
]


def test_levels():
    for prompt, expected in CASES:
        level, _ = classify(prompt)
        assert level == expected, f"{prompt!r}: got {level}, expected {expected}"


def test_directive_and_badge_for_each_level():
    for lvl in ("LOW", "MEDIUM", "HIGH", "MAX"):
        assert directive(lvl)
        assert ICON[lvl] in badge(lvl, "reason")


def test_empty_is_medium():
    assert classify("")[0] == "MEDIUM"


if __name__ == "__main__":
    test_levels()
    test_directive_and_badge_for_each_level()
    test_empty_is_medium()
    print(f"OK — {len(CASES)} classification cases + directives/badges + empty all pass.")
