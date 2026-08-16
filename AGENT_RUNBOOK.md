# Agent Runbook

Run commands from this repository's root.

## Step 0 — Confirm scope and authority

Read [`AGENTS.md`](AGENTS.md) and
[`ANNOTATION_STANDARD.md`](ANNOTATION_STANDARD.md). Zotero writes require an
explicit user request; a request to annotate or tag specified papers is enough
authority for those items, not for unrelated library changes.

When a Zotero integration or skill is available, use its supported status
helper. Otherwise probe the local API read-only:

```bash
curl -fsS http://127.0.0.1:23119/api/
```

## Step 1 — Check prerequisites

```bash
command -v pdftotext
python3 --version
```

For the optional X11 runner:

```bash
command -v xclip
command -v wmctrl
```

Zotero Desktop must be open and unlocked, its local API must answer at
`http://127.0.0.1:23119`, and each PDF attachment must be available locally.

## Step 2 — Resolve Zotero items without touching SQLite

Identify for every paper:

- parent bibliographic item key;
- PDF attachment key;
- exact parent title;
- absolute local PDF path.

A Zotero item key and a BibTeX citation key are different. The manifest uses
Zotero item keys.

Useful read-only routes:

```text
GET /api/users/0/items/<PARENT_KEY>
GET /api/users/0/items/<PARENT_KEY>/children
GET /api/users/0/items/<ATTACHMENT_KEY>/file/view/url
GET /api/users/0/items?itemType=annotation&limit=100&start=0
```

Paginate until a response contains fewer than the requested `limit`; never
assume the first 100 results are the entire library.

## Step 3 — Read and author a manifest

Read the PDF directly. `pdftotext -layout` is useful for text review. Render a
page when layout, equations, figures, or multi-column reading order matter.

Start from [`example_manifest.json`](example_manifest.json). Use a reviewable
patch or editor and preserve unrelated entries. The schema is:

```json
{
  "papers": [
    {
      "parentKey": "ABCDEFGH",
      "attachmentKey": "HGFEDCBA",
      "title": "Exact Zotero Parent Title",
      "pdfPath": "/absolute/path/to/paper.pdf",
      "concepts": [
        {
          "heading": "Short Vietnamese heading",
          "text": "Exact contiguous English PDF sentence.",
          "note": "Beginner-friendly Vietnamese explanation..."
        }
      ]
    }
  ]
}
```

The writer enforces at least eight words in a highlight and 180 stripped
characters in a note. These are minimum guards, not a quality target.

## Step 4 — Validate and generate annotation JavaScript

Select exact parent keys for each modest-sized batch:

```bash
python3 annotate_from_manual_manifest.py annotations.json \
  --paper PARENT_KEY_1 \
  --paper PARENT_KEY_2 \
  > /tmp/zotero_annotations.js
```

Validation checks:

- parent title and attachment relationship match Zotero;
- PDF exists;
- attachment has no existing annotations;
- every passage has one unique normalized match on one PDF page;
- note and highlight minimum lengths pass.

Read stderr. It must report the intended number of papers and pairs. Inspect
the generated JavaScript whenever the scope is surprising.

## Step 5 — Write through Zotero

Open **Tools -> Developer -> Run JavaScript** in Zotero. Paste and run
`/tmp/zotero_annotations.js` manually, or use:

```bash
python3 run_js_in_zotero.py /tmp/zotero_annotations.js --yes
```

The payload uses `Zotero.Annotations.saveFromJSON`; it does not modify the PDF
file or SQLite directly. The UI helper submits a payload but does not prove it
succeeded.

## Step 6 — Verify before tagging

```bash
python3 audit_manifest.py annotations.json \
  --paper PARENT_KEY_1 \
  --paper PARENT_KEY_2
```

A strict audit requires:

- exact expected highlight text;
- exact expected numbered note text;
- equal expected highlight and note counts;
- no unexpected annotations on those attachments;
- no blank annotation;
- no annotation-level tag;
- correct parent/attachment linkage.

Open representative PDF pages in Zotero as a visual geometry check. Do not tag
the batch if either content or visual verification fails.

## Step 7 — Generate and apply parent tags

Only after Step 6 succeeds:

```bash
python3 annotate_from_manual_manifest.py annotations.json \
  --paper PARENT_KEY_1 \
  --paper PARENT_KEY_2 \
  --tags > /tmp/zotero_tags.js

python3 run_js_in_zotero.py /tmp/zotero_tags.js --yes

python3 audit_manifest.py annotations.json \
  --paper PARENT_KEY_1 \
  --paper PARENT_KEY_2 \
  --require-parent-tag 'need to read'
```

The tag payload preserves existing parent tags and adds `need to read` only if
missing.

## Step 8 — Report precisely

Report:

- number of papers processed;
- number of highlight/note pairs written;
- whether exact content and tag audits passed;
- whether representative geometry was visually inspected;
- any pre-existing irregularities left untouched;
- manifest path and revision.

Do not claim a whole collection is complete unless a collection-wide audit
actually established that fact.
