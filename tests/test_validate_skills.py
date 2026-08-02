from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import unittest.mock

from scripts import validate_skills
from scripts.validate_skills import validate


ROOT = Path(__file__).resolve().parents[1]


def _contract_tool_names() -> list[str]:
    contract = json.loads(
        (ROOT / "references" / "tubealfred-tools.json").read_text(encoding="utf-8")
    )
    return [tool["mcp_tool"] for tool in contract["tools"]]


class SkillValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "references").mkdir()
        (self.root / "references" / "tubealfred-tools.json").write_text(
            (ROOT / "references" / "tubealfred-tools.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    HOST_METADATA = (
        '{"openclaw":{"emoji":"▶️","requires":{"env":["TUBEALFRED_API_KEY"]},'
        '"primaryEnv":"TUBEALFRED_API_KEY","homepage":"https://tubealfred.com"},'
        '"hermes":{"tags":["youtube","video"],"category":"media"}}'
    )

    def write_skill(
        self,
        body: str,
        metadata: str | None = None,
        description: str = (
            "Inspect one public YouTube video. Use when a factual metadata snapshot is needed. "
            "Do not use for transcript or comment analysis."
        ),
        version: str = "2.0.0",
        host_metadata: str | None = None,
    ) -> None:
        skill = self.root / "skills" / "example-skill"
        (skill / "agents").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: example-skill\n"
            f'description: "{description}"\n'
            f'version: "{version}"\n'
            f"metadata: {host_metadata or self.HOST_METADATA}\n"
            "---\n\n"
            + body,
            encoding="utf-8",
        )
        (skill / "agents" / "openai.yaml").write_text(
            metadata
            or "interface:\n"
            '  display_name: "Example Skill"\n'
            '  short_description: "Inspect public YouTube metadata"\n'
            '  default_prompt: "Use $example-skill to inspect one YouTube video."\n',
            encoding="utf-8",
        )

    def errors(
        self,
        require_tool_coverage: bool = False,
        require_canonical_blocks: bool = False,
    ) -> list[str]:
        return validate(
            self.root,
            self.root / "references" / "tubealfred-tools.json",
            require_agents=True,
            require_tool_coverage=require_tool_coverage,
            require_canonical_blocks=require_canonical_blocks,
        )

    def test_accepts_valid_skill_and_metadata(self) -> None:
        self.write_skill(
            "# Example\n\nCall `youtube_video_get` or `GET /v1/youtube/video/{video_id}`.\n"
        )
        self.assertEqual([], self.errors())

    def test_rejects_unknown_tool_and_rest_operation(self) -> None:
        self.write_skill(
            "# Example\n\nCall `youtube_invented_tool` or `GET /v1/youtube/invented`.\n"
        )
        message = "\n".join(self.errors())
        self.assertIn("unknown TubeAlfred MCP tool", message)
        self.assertIn("unknown TubeAlfred REST operation", message)

    def test_rejects_broken_local_link(self) -> None:
        self.write_skill("# Example\n\nRead [missing](references/missing.md).\n")
        self.assertIn("broken local link", "\n".join(self.errors()))

    def test_rejects_invalid_agent_prompt(self) -> None:
        self.write_skill(
            "# Example\n\nCall `youtube_video_get`.\n",
            "interface:\n"
            '  display_name: "Example Skill"\n'
            '  short_description: "Inspect public YouTube metadata"\n'
            '  default_prompt: "Inspect one YouTube video."\n',
        )
        self.assertIn("must mention $example-skill", "\n".join(self.errors()))

    def test_rejects_missing_negative_routing_boundary(self) -> None:
        self.write_skill(
            "# Example\n\nCall `youtube_video_get`.\n",
            description=(
                "Inspect one public YouTube video. Use when a factual metadata snapshot is needed."
            ),
        )
        self.assertIn("negative routing boundary", "\n".join(self.errors()))

    def test_reports_contract_tool_no_skill_references(self) -> None:
        self.write_skill("# Example\n\nCall `youtube_video_get`.\n")
        message = "\n".join(self.errors(require_tool_coverage=True))
        self.assertIn("'youtube_video_transcript' is referenced by no skill", message)
        # The one tool the fixture skill does reference must not be reported.
        self.assertNotIn("'youtube_video_get' is referenced by no skill", message)

    def test_allowed_unused_tools_suppresses_coverage_error(self) -> None:
        self.write_skill("# Example\n\nCall `youtube_video_get`.\n")
        declared = {
            name: "test fixture"
            for name in _contract_tool_names()
            if name != "youtube_video_get"
        }
        with unittest.mock.patch.object(
            validate_skills, "ALLOWED_UNUSED_TOOLS", declared
        ):
            self.assertEqual([], self.errors(require_tool_coverage=True))

    def test_rejects_declaring_a_referenced_tool_as_unused(self) -> None:
        self.write_skill("# Example\n\nCall `youtube_video_get`.\n")
        declared = {name: "test fixture" for name in _contract_tool_names()}
        with unittest.mock.patch.object(
            validate_skills, "ALLOWED_UNUSED_TOOLS", declared
        ):
            message = "\n".join(self.errors(require_tool_coverage=True))
        self.assertIn("is declared unused but a skill references it", message)

    def test_rejects_unknown_tool_in_allowed_unused(self) -> None:
        self.write_skill("# Example\n\nCall `youtube_video_get`.\n")
        with unittest.mock.patch.object(
            validate_skills, "ALLOWED_UNUSED_TOOLS", {"youtube_invented": "nope"}
        ):
            message = "\n".join(self.errors(require_tool_coverage=True))
        self.assertIn("names unknown tool 'youtube_invented'", message)

    def skeleton_body(self, order: list[str] | None = None) -> str:
        """A minimal body carrying every canonical section and block."""
        sections = order or validate_skills.CANONICAL_SECTIONS
        blocks = {
            "## Safety and access": validate_skills.CANONICAL_BLOCKS["safety and access"],
            "## Errors and stop conditions": validate_skills.CANONICAL_BLOCKS[
                "HTTP failure handling"
            ],
        }
        body = "# Example\n\nCall `youtube_video_get`.\n\n"
        for section in sections:
            body += f"{section}\n\n{blocks.get(section, 'Body text.')}\n\n"
        return body

    def test_accepts_verbatim_canonical_blocks(self) -> None:
        self.write_skill(self.skeleton_body())
        self.assertEqual([], self.errors(require_canonical_blocks=True))

    def test_rejects_reordered_sections(self) -> None:
        order = list(validate_skills.CANONICAL_SECTIONS)
        order[1], order[2] = order[2], order[1]
        self.write_skill(self.skeleton_body(order))
        self.assertIn("canonical sections are out of order", "\n".join(
            self.errors(require_canonical_blocks=True)
        ))

    def test_rejects_missing_required_section(self) -> None:
        order = [s for s in validate_skills.CANONICAL_SECTIONS if s != "## Evidence rules"]
        self.write_skill(self.skeleton_body(order))
        self.assertIn("missing required section '## Evidence rules'", "\n".join(
            self.errors(require_canonical_blocks=True)
        ))

    def test_allows_omitting_the_optional_interface_section(self) -> None:
        order = [
            s for s in validate_skills.CANONICAL_SECTIONS
            if s not in validate_skills.OPTIONAL_SECTIONS
        ]
        self.write_skill(self.skeleton_body(order))
        self.assertEqual([], self.errors(require_canonical_blocks=True))

    def test_ignores_headings_inside_fenced_examples(self) -> None:
        body = self.skeleton_body() + "```markdown\n## Not a real section\n```\n"
        self.write_skill(body)
        self.assertEqual([], self.errors(require_canonical_blocks=True))

    def test_rejects_drifted_canonical_block(self) -> None:
        blocks = "\n\n".join(validate_skills.CANONICAL_BLOCKS.values())
        # One reworded clause is exactly the drift this check exists to catch.
        drifted = blocks.replace("wait until `X-RateLimit-Reset`", "wait a moment")
        self.write_skill(f"# Example\n\nCall `youtube_video_get`.\n\n{drifted}\n")
        message = "\n".join(self.errors(require_canonical_blocks=True))
        self.assertIn("canonical HTTP failure handling block", message)

    def test_rejects_missing_canonical_block(self) -> None:
        self.write_skill("# Example\n\nCall `youtube_video_get`.\n")
        message = "\n".join(self.errors(require_canonical_blocks=True))
        self.assertIn("canonical safety and access block", message)
        self.assertIn("canonical HTTP failure handling block", message)

    def test_shipped_catalog_passes_every_check(self) -> None:
        self.assertEqual(
            [],
            validate(
                ROOT,
                ROOT / "references" / "tubealfred-tools.json",
                require_agents=True,
                require_tool_coverage=True,
                require_canonical_blocks=True,
            ),
        )

    def test_rejects_non_semver_version(self) -> None:
        self.write_skill("# Example\n\nCall `youtube_video_get`.\n", version="2.0")
        self.assertIn("version must be MAJOR.MINOR.PATCH", "\n".join(self.errors()))

    def test_rejects_version_disagreeing_with_version_file(self) -> None:
        self.write_skill("# Example\n\nCall `youtube_video_get`.\n", version="2.0.0")
        (self.root / "VERSION").write_text("3.0.0\n", encoding="utf-8")
        self.assertIn("no skill carries that version", "\n".join(self.errors()))

    def test_rejects_malformed_host_metadata(self) -> None:
        self.write_skill(
            "# Example\n\nCall `youtube_video_get`.\n",
            host_metadata='{"openclaw":{"emoji":"▶️"},"hermes":{"tags":[],"category":"nope"}}',
        )
        message = "\n".join(self.errors())
        self.assertIn("metadata.openclaw.primaryEnv", message)
        self.assertIn("metadata.hermes.tags must be a non-empty list", message)
        self.assertIn("metadata.hermes.category must be one of", message)

    def test_rejects_committed_api_key_shape(self) -> None:
        self.write_skill("# Example\n\nCall `youtube_video_get`.\n")
        (self.root / "accidental.txt").write_text(
            "ta_" + "live_" + "abcdefghijklmnop", encoding="utf-8"
        )
        self.assertIn("possible TubeAlfred API key", "\n".join(self.errors()))


if __name__ == "__main__":
    unittest.main()
