## Change

Describe the user-visible skill behavior or contract change.

## Evidence

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `python3 scripts/validate_skills.py`
- [ ] If TubeAlfred's API changed, I regenerated the contract with `python3 scripts/sync_contract.py --openapi https://tubealfred.com/openapi.json --pinned-on YYYY-MM-DD`.
- [ ] Expensive calls require explicit approval, and examples do not expose credentials.
- [ ] New conclusions are supported by the data fetched or clearly labeled as unavailable/inferred.
