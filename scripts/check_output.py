#!/usr/bin/env python3
"""Check a skill's produced output for the judgment rules the skills promise.

`validate_skills.py` checks that a SKILL.md is well formed.  It cannot check
that following the skill produces an honest artifact.  This script closes that
gap from the other end: run a skill against a known response, paste the output
here with the response it was built from, and the rules below fail on the
mistakes these skills exist to prevent — an unlabeled claim, a derived figure
presented as observed, a number that appears in no response, a paid comment
call with no spend gate, or a thumbnail critique with no pixels behind it.

    python3 scripts/check_output.py --output brief.md \\
        --response tests/fixtures/responses/video_get.json

Exits non-zero and prints one line per violation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

LABELS = ("[Observed]", "[Calculated]", "[Inferred]", "[Unavailable]")
LABEL_RE = re.compile(r"\[(?:Observed|Calculated|Inferred|Unavailable)[^\]]*\]")
OBSERVED_RE = re.compile(r"\[Observed[^\]]*\]")
BULLET_RE = re.compile(r"^\s*[-*]\s+(.*)$")
NUMBER_RE = re.compile(r"(?<![\w:.])\d[\d,]*(?:\.\d+)?(?![\d:])")
TIMESTAMP_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")

# Wording that means the figure was derived rather than read off a response.
# Word markers are matched on word boundaries: "duration_seconds" contains
# "ratio", and a substring test would flag an honest observation.
DERIVED_RE = re.compile(
    r"[=÷%]|\bmedian\b|\bmean\b|\baverage\b|\bratio\b|\bper day\b|\bpercent\w*\b"
    r"|\bsum\(|\btotal of\b",
    re.I,
)

# Sections whose bullets are instructions or caveats, not evidence claims.
EXEMPT_HEADINGS = ("limits", "limitations", "caveats", "actions", "opportunities",
                   "recommended actions", "reply angles", "title concepts",
                   "next steps", "priority fixes")

COMMENT_CALL_MARKERS = (
    "youtube_comments_list",
    "youtube_comments_page",
    "youtube_replies_list",
    "youtube_replies_page",
    "/comments",
)
SPEND_GATE_RE = re.compile(r"(at least 20 credits|max\(20|20-credit minimum)", re.I)

QUOTE_RE = re.compile(r"[\"“]([^\"”]{12,})[\"”]")

THUMBNAIL_CLAIM_RE = re.compile(
    r"thumbnail[^.\n]*\b(composition|legib|contrast|face|colou?r|text|crop|framing)",
    re.I,
)


class Violation:
    def __init__(self, rule: str, line_number: int, line: str, detail: str) -> None:
        self.rule = rule
        self.line_number = line_number
        self.line = line
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.rule} (line {self.line_number}): {self.detail}\n    {self.line.strip()}"


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


def _iter_numbers(value: Any) -> Iterable[str]:
    """Every numeric token a response could legitimately support."""
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float)):
        text = f"{value}"
        yield text
        if text.endswith(".0"):
            yield text[:-2]
        return
    if isinstance(value, str):
        for match in NUMBER_RE.finditer(value):
            yield match.group(0).replace(",", "")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from _iter_numbers(item)


def _content_lines(text: str) -> list[tuple[int, str, str, int]]:
    """Lines outside code fences, tagged with heading and paragraph index.

    The paragraph index lets the spend gate be satisfied by the same sentence
    that names the call, which is how an author naturally writes it.
    """
    rows: list[tuple[int, str, str, int]] = []
    fenced = False
    heading = ""
    paragraph = 0
    for number, line in enumerate(text.split("\n"), 1):
        if line.startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if not line.strip():
            paragraph += 1
            continue
        if line.startswith("#"):
            heading = line.lstrip("#").strip().lower()
            paragraph += 1
            continue
        rows.append((number, line, heading, paragraph))
    return rows


def check(output: str, responses: list[dict[str, Any]]) -> list[Violation]:
    violations: list[Violation] = []
    supported = {token for response in responses for token in _iter_numbers(response)}
    source_text = " || ".join(
        _normalize(value) for response in responses for value in _iter_strings(response)
    )
    rows = _content_lines(output)

    header = "\n".join(line for _, line, _, _ in rows[:12])
    for field in ("Source:", "Retrieved:"):
        if field not in header:
            violations.append(
                Violation("missing-coverage-header", 1, header.split("\n")[0],
                          f"the output must open with a {field} line naming its provenance")
            )

    gate_lines = [number for number, line, _, _ in rows if SPEND_GATE_RE.search(line)]
    gate_paragraphs = {
        paragraph for _, line, _, paragraph in rows if SPEND_GATE_RE.search(line)
    }
    first_gate = gate_lines[0] if gate_lines else None
    for number, line, heading, paragraph in rows:
        stripped = line.strip()
        if not stripped:
            continue

        bullet = BULLET_RE.match(line)
        is_claim = bool(bullet) and heading not in EXEMPT_HEADINGS
        labels = LABEL_RE.findall(line)

        if is_claim and not labels:
            violations.append(
                Violation("unlabeled-claim", number, line,
                          "every evidence bullet needs one of " + ", ".join(LABELS))
            )

        if OBSERVED_RE.search(line):
            if DERIVED_RE.search(line):
                violations.append(
                    Violation("observed-on-derived", number, line,
                              "a derived figure is [Calculated], never [Observed]")
                )
            else:
                without_timestamps = TIMESTAMP_RE.sub(" ", line)
                for match in NUMBER_RE.finditer(without_timestamps):
                    token = match.group(0).replace(",", "")
                    if token not in supported:
                        violations.append(
                            Violation("untraceable-number", number, line,
                                      f"{token!r} appears in no supplied response")
                        )

        for quote in QUOTE_RE.findall(line):
            if _normalize(quote) and _normalize(quote) not in source_text:
                violations.append(
                    Violation("unquotable-excerpt", number, line,
                              "the quoted text appears in no supplied response")
                )

        if any(marker in line for marker in COMMENT_CALL_MARKERS):
            gated = paragraph in gate_paragraphs or (
                first_gate is not None and first_gate <= number
            )
            if not gated:
                violations.append(
                    Violation("missing-spend-gate", number, line,
                              "a comment or reply call must be preceded by its "
                              "stated 20-credit minimum")
                )

        if THUMBNAIL_CLAIM_RE.search(line) and "[Unavailable]" not in line:
            violations.append(
                Violation("unsupported-thumbnail-claim", number, line,
                          "thumbnail composition is [Unavailable] unless pixels "
                          "were actually inspected")
            )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="Markdown a skill produced")
    parser.add_argument("--response", type=Path, action="append", default=[],
                        help="JSON response the output was built from (repeatable)")
    args = parser.parse_args()

    responses = [json.loads(path.read_text(encoding="utf-8")) for path in args.response]
    violations = check(args.output.read_text(encoding="utf-8"), responses)
    if violations:
        print("\n".join(str(violation) for violation in violations), file=sys.stderr)
        return 1
    print(f"OK: {args.output} satisfies the evidence rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
