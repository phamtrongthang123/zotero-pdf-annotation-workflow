# Zotero PDF Annotation Workflow

A manual-first, verifiable workflow for adding meaningful PDF highlights and
paired explanatory notes to Zotero Desktop.

The intended annotation style is:

- exact English highlights covering complete sentences or a short coherent
  paragraph;
- beginner-friendly Vietnamese notes that retain and explain important English
  terminology;
- an optional `need to read` tag on the parent bibliographic item, applied only
  after annotation verification.

The scripts automate text-to-PDF geometry, Zotero writes, and audits. They do
**not** decide what a paper means. A human or capable reading agent must read
the relevant paper context, select the passage, and author the explanation.

## Why this exists

Browser automation is fragile, and direct edits to `zotero.sqlite` are unsafe.
This workflow instead uses:

1. a reviewable JSON manifest containing scholarly decisions;
2. Poppler word boxes to locate exact text on a PDF page;
3. Zotero's own JavaScript object API to create annotations;
4. Zotero's read-only local API to verify exact content afterward.

## Requirements

- Zotero Desktop with its local API enabled;
- Python 3.10 or newer;
- Poppler's `pdftotext`;
- `wmctrl` and `xclip` for the optional X11 UI runner;
- an X11 desktop session for automated paste/run. Manual execution remains
  available on Wayland or other platforms.

No Python packages outside the standard library are required.

## Quick start

1. Read [`ANNOTATION_STANDARD.md`](ANNOTATION_STANDARD.md).
2. Copy [`example_manifest.json`](example_manifest.json) to a user-owned
   manifest and fill it after reading the PDFs.
3. Open Zotero's **Tools -> Developer -> Run JavaScript** window.
4. Generate and submit annotation JavaScript:

   ```bash
   python3 annotate_from_manual_manifest.py annotations.json \
     --paper PARENT_KEY > /tmp/zotero_annotations.js
   python3 run_js_in_zotero.py /tmp/zotero_annotations.js --yes
   ```

5. Verify exact contents:

   ```bash
   python3 audit_manifest.py annotations.json --paper PARENT_KEY
   ```

6. Only after verification, generate and submit the tag payload:

   ```bash
   python3 annotate_from_manual_manifest.py annotations.json \
     --paper PARENT_KEY --tags > /tmp/zotero_tags.js
   python3 run_js_in_zotero.py /tmp/zotero_tags.js --yes
   python3 audit_manifest.py annotations.json --paper PARENT_KEY \
     --require-parent-tag 'need to read'
   ```

See [`AGENT_RUNBOOK.md`](AGENT_RUNBOOK.md) for the complete procedure and
[`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) before recovering a partial write.

## Files

- [`annotate_from_manual_manifest.py`](annotate_from_manual_manifest.py):
  validates the manifest, resolves exact PDF geometry, and emits Zotero
  JavaScript for annotations or parent tags.
- [`audit_manifest.py`](audit_manifest.py): verifies exact annotation text,
  note text, counts, tags, and parent/attachment relationships.
- [`run_js_in_zotero.py`](run_js_in_zotero.py): optional X11 helper that pastes
  an explicitly selected JavaScript file into Zotero and runs it.
- [`example_manifest.json`](example_manifest.json): non-executable schema
  example.
- [`ANNOTATION_STANDARD.md`](ANNOTATION_STANDARD.md): reading and writing
  quality criteria.
- [`AGENT_RUNBOOK.md`](AGENT_RUNBOOK.md): step-by-step operational guide.
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md): failure and recovery rules.

## Safety model

- Never edit `zotero.sqlite` directly.
- Use Zotero's local API only for reads; it does not support annotation writes.
- Use Zotero object APIs for writes.
- Never rerun a partially written batch blindly.
- Preserve existing annotations and tags.
- Tag parent bibliographic items only; leave annotation tags empty.
- Treat generated JavaScript as a write payload: inspect its scope and execute
  only under an explicit user request.

The initial workflow was exercised with Zotero 9.0.6 on Linux/X11. Zotero's
internal JavaScript APIs are not a stable public compatibility promise, so
revalidate the write path after major Zotero upgrades.
