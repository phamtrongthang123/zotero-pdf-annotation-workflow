# Agent Instructions

Before modifying or using this workflow, read in order:

1. `README.md`
2. `ANNOTATION_STANDARD.md`
3. `AGENT_RUNBOOK.md`
4. `TROUBLESHOOTING.md`

## Non-negotiable rules

- Scholarly judgment is manual: read the relevant PDF context before selecting
  any passage or writing a note.
- Highlights are exact, contiguous, and normally contain complete sentences.
- Notes explain concepts to a newcomer and state claim boundaries.
- Never edit `zotero.sqlite`.
- Zotero writes require an explicit user request.
- Verify exact annotation contents before applying parent tags.
- Preserve existing user annotations and tags.
- Never blindly rerun a partial batch.
- Do not commit real manifests containing private titles, notes, item keys, or
  absolute PDF paths unless the user explicitly requests publication.

Use patch-based edits for reviewability and run the unit tests before pushing.
