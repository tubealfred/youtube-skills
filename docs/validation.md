# Validation boundaries

`python3 scripts/validate_skills.py` checks:

- strict `name` and `description` frontmatter;
- skill name, directory match, body size, and uniqueness;
- MCP tool names and REST operations against the 34-tool pinned contract;
- one-line MCP-to-REST mappings when both appear together;
- local Markdown links;
- required `agents/openai.yaml` interface metadata and local icon paths;
- that every contract tool is reachable from at least one skill, unless it is declared in `ALLOWED_UNUSED_TOOLS` with a reason;
- that the shared safety and HTTP failure text is byte-identical across all fifteen skills, against the canonical wording in `CANONICAL_BLOCKS`;
- that every skill carries the `CANONICAL_SECTIONS` skeleton in order, ignoring `##` lines inside fenced examples; and
- text files for TubeAlfred credential-shaped strings.

`python3 -m unittest discover -s tests -v` exercises contract extraction, known validator failure cases, and the golden-output fixtures below. `python3 scripts/sync_contract.py --check` fetches the official versioned operation manifest and fails when the generated contract or catalog would differ.

## Checking a produced artifact

Structural validation cannot tell whether following a skill produced an honest artifact. `scripts/check_output.py` works from the other end — give it a skill's output and the responses it was built from:

```bash
python3 scripts/check_output.py --output brief.md \
  --response tests/fixtures/responses/video_get.json
```

It fails on six mistakes these skills exist to prevent: an unlabeled evidence claim, a derived figure presented as `[Observed]`, a number or quoted excerpt appearing in no response, a comment/reply call with no preceding spend gate, a missing provenance header, and a thumbnail critique with no pixels behind it.

`tests/fixtures/outputs/` pins this with a `.good.md` and `.bad.md` pair per covered skill, so a change that weakens the rules fails the test suite.

The checker verifies traceability and shape, **not** semantics: a fabricated paraphrase that quotes nothing and invents no number will pass. Treat a clean run as "this artifact did not overclaim in a mechanically detectable way," not as "this artifact is correct."

These checks do **not** prove:

- that YouTube currently returns data for a specific resource;
- that TubeAlfred credentials, credits, OAuth, or upstream YouTube are available;
- semantic correctness of every recommendation;
- trigger quality in every agent host; or
- user approval for real paid calls.

Those properties require fixture-based forward tests, host-specific trigger evaluations, and carefully bounded live smoke tests. Live data tests must use an authorized test account, disclose the expected credit spend, and never run automatically for pull requests from forks.
