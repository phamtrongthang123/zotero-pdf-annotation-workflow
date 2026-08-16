# Troubleshooting and Recovery

## Local API is unavailable

Symptoms include connection refused on port `23119` or `api_running: false`.

1. Confirm Zotero Desktop is open and unlocked.
2. Run the Zotero skill's `status --json` helper.
3. If the local API preference is disabled, use the skill's supported enable
   command and restart Zotero only when the user has asked you to operate it.
4. Do not fall back to querying `zotero.sqlite`.

## Quote has zero matches

The geometry writer normalizes case, punctuation, accents, and whitespace, but
the selected alphanumeric sequence must still be contiguous on one page.
Common causes:

- copied text differs from the actual attached PDF version;
- a sentence crosses a page boundary;
- a citation or parenthetical phrase was omitted;
- PDF extraction changed ligatures or hyphenated words;
- multi-column extraction order differs from visual order.

Inspect the relevant page with `pdftotext -bbox-layout` or render it. Correct
the manifest quote; do not weaken the writer to accept an approximate match.

## Quote has multiple matches

Extend the quote with an adjacent complete sentence or a distinguishing clause
until the normalized match is unique. Do not select an arbitrary occurrence.

## `Attachment already annotated`

This guard prevents duplicates and preserves user annotations. Inspect the
attachment through the local API. Determine whether it was processed earlier,
contains the user's annotations, or contains a partial failed batch.

Do not bypass the guard merely to rerun. The `--tags` path allows existing
annotations only because it does not create annotations.

## Partial JavaScript write

The writer saves one annotation at a time; a crash can leave a partial batch.

1. Stop. Do not rerun the batch.
2. Fetch all annotation children for the exact attachment.
3. Compare their text/comments with the manifest.
4. Preserve unrelated existing annotations.
5. If deletion or repair is needed, ask for explicit authorization and target
   exact annotation keys. Prefer a small repair script using Zotero object APIs.
6. Audit again before tagging.

## Run JavaScript window is not found

Open **Tools -> Developer -> Run JavaScript** in Zotero and rerun the helper.
If window automation is unreliable, paste the generated JavaScript manually.
The generated file is the authoritative payload; UI automation is merely a
convenience.

## Highlight geometry looks wrong

API content checks cannot prove visual placement. Open the affected PDF page
in Zotero and visually inspect representative highlights, especially for:

- rotated pages;
- two-column layouts;
- tables, captions, or footnotes;
- unusual CropBox/MediaBox geometry;
- OCR-only or malformed PDFs.

If geometry is wrong, do not tag the paper as complete. Repair the locator or
create precise annotations through Zotero before continuing.

## Counts are imbalanced

For a new manifest-driven attachment, the expected count is one highlight and
one note per concept. Imbalance means a partial write, an existing annotation,
or a manual edit. Inspect exact contents rather than deleting the surplus.

Older manually annotated papers can legitimately be imbalanced. Record the
irregularity and preserve it unless the user asks for normalization.

## Desktop session is Wayland-only

`run_js_in_zotero.py` uses X11 tools (`wmctrl`, `xclip`, and XTest). It may not
control a native Wayland window. Use manual paste/run, or implement a supported
Wayland route without weakening the verification steps.
