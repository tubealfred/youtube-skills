"""The judgment checker must pass honest artifacts and fail dishonest ones.

Structural validation cannot tell whether a skill's output earned its claims.
These fixtures pin that behaviour: each `.good.md` is an artifact the skill
should produce from the paired response, and each `.bad.md` commits exactly the
mistakes the skill's evidence rules forbid.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from scripts.check_output import check


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "tests" / "fixtures" / "outputs"
RESPONSES = ROOT / "tests" / "fixtures" / "responses"

PAIRS = {
    "youtube-video": ["video_get"],
    "youtube-comments": ["comments_list"],
    "youtube-transcript": ["transcript_fast"],
}


def run(output_name: str, response_names: list[str]) -> list[str]:
    responses = [
        json.loads((RESPONSES / f"{name}.json").read_text(encoding="utf-8"))
        for name in response_names
    ]
    output = (OUTPUTS / f"{output_name}.md").read_text(encoding="utf-8")
    return [violation.rule for violation in check(output, responses)]


class GoldenOutputTests(unittest.TestCase):
    def test_honest_outputs_pass_every_rule(self) -> None:
        for skill, responses in PAIRS.items():
            with self.subTest(skill=skill):
                self.assertEqual([], run(f"{skill}.good", responses))

    def test_video_output_is_caught_inventing_and_overclaiming(self) -> None:
        rules = run("youtube-video.bad", PAIRS["youtube-video"])
        self.assertIn("untraceable-number", rules)
        self.assertIn("observed-on-derived", rules)
        self.assertIn("unlabeled-claim", rules)
        self.assertIn("unsupported-thumbnail-claim", rules)

    def test_comment_output_is_caught_skipping_the_spend_gate(self) -> None:
        self.assertIn(
            "missing-spend-gate", run("youtube-comments.bad", PAIRS["youtube-comments"])
        )

    def test_transcript_output_is_caught_fabricating_a_quote(self) -> None:
        rules = run("youtube-transcript.bad", PAIRS["youtube-transcript"])
        self.assertIn("unquotable-excerpt", rules)
        self.assertIn("missing-coverage-header", rules)

    def test_every_fixture_output_has_a_paired_response(self) -> None:
        for path in sorted(OUTPUTS.glob("*.md")):
            skill = path.name.split(".")[0]
            with self.subTest(output=path.name):
                self.assertIn(skill, PAIRS)


if __name__ == "__main__":
    unittest.main()
