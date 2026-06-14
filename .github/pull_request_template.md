## Summary

-

## Verification

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py`
- [ ] Documentation updated, if user-facing behavior changed

## Boundary Check

- [ ] This preserves the "workflow adaptation, not model replacement" boundary.
- [ ] This does not add credentials, private prompt text, or hidden provider assumptions.
- [ ] Current product/provider/API claims are backed by official sources when applicable.

