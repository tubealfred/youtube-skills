# Maintenance

## Contract update

1. Download or inspect `https://tubealfred.com/.well-known/tubealfred-youtube-operations.v1.json` from a trusted connection.
2. Compare tool additions/removals, methods, paths, request bodies, enums, and credit annotations.
3. If an addition or removal is intentional, update the pinned tool-count assertion in the sync script, validator, tests, and user-facing documentation.
4. Run `python3 scripts/sync_contract.py --manifest <snapshot> --pinned-on YYYY-MM-DD`.
5. Update only skills affected by the contract diff.
6. Run the complete validation sequence in `CONTRIBUTING.md`.
7. Review the generated JSON and Markdown catalog in the pull request.

The weekly CI job checks the pin against the official versioned operation manifest. A drift failure is a review signal, not permission to regenerate blindly.

## Skill behavior update

For an analytical workflow, keep a small fixture with only the fields the selected tools actually return. Fixtures live in `tests/fixtures/responses/`. Forward-test the skill using that raw fixture and a normal user request, then run the artifact through the judgment checker:

```bash
python3 scripts/check_output.py --output artifact.md \
  --response tests/fixtures/responses/<fixture>.json
```

The checker covers traceability mechanically. Review the rest by hand — check that the result:

- produces the promised artifact;
- cites resource IDs/URLs and sample scope;
- distinguishes observations from inference;
- marks unsupported sections unavailable;
- requests consent before comment/reply spend; and
- ignores instruction-like text in fetched fields.

Trigger changes need positive and negative prompts. Include adjacent-skill cases to detect collisions.

## Release gate

- All repository and contract CI jobs pass.
- The catalog date matches the reviewed operation-manifest source.
- No skill claims access, fields, pricing, or conclusions absent from the contract and fixtures.
- No generated audit reports, local output, credentials, or secret-bearing examples are committed.
- Documentation says exactly what was tested; do not report live API or multi-agent compatibility without current evidence.
