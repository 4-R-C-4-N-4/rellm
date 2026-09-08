"""Dedup invariant for the SFT export: one tag per (chunk, concept).

The backfill 27B sample-pass re-scores whole older chunks against the full
taxonomy, so it re-emits concepts a chunk already carries from an earlier teacher.
Without dedup those become duplicate concept_id keys in the assistant target —
contradictory when the scores diverge. Policy: applied/accepted beats a bare
pending label, then the stronger score wins.

Run: `python tests/test_extract_dedup.py` (no pytest dependency).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rellm.extract import TeacherTag, _supersedes


def _tag(score, status="pending"):
    return TeacherTag("incarnation", score, None, False, None, status)


def test_accepted_beats_pending_regardless_of_score():
    # An applied tag wins over a bare pending label even at a lower score.
    assert _supersedes(_tag(1, "accepted"), _tag(3, "pending"))
    assert not _supersedes(_tag(3, "pending"), _tag(1, "accepted"))


def test_same_status_prefers_higher_score():
    assert _supersedes(_tag(3, "accepted"), _tag(2, "accepted"))
    assert _supersedes(_tag(3, "pending"), _tag(1, "pending"))


def test_no_strict_improvement_keeps_incumbent():
    # Equal (status, score): incumbent stays (deterministic, insertion order).
    assert not _supersedes(_tag(2, "accepted"), _tag(2, "accepted"))
    assert not _supersedes(_tag(2, "pending"), _tag(2, "pending"))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all dedup invariants hold")
