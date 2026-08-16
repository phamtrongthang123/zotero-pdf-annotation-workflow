#!/usr/bin/env python3
"""Generate Zotero JavaScript from manually selected PDF sentences.

The manifest contains decisions made after reading each paper: exact English
quotations and explanatory notes. This script performs geometry lookup and
JavaScript generation only. It never edits zotero.sqlite or a PDF.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


LOCAL_API = "http://127.0.0.1:23119/api/users/0"


def normalize(text: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", text).lower()
        if character.isalnum()
    )


def api_get(path: str):
    with urllib.request.urlopen(f"{LOCAL_API}{path}", timeout=20) as response:
        return json.load(response)


def all_annotations() -> list[dict]:
    records: list[dict] = []
    start = 0
    while True:
        batch = api_get(
            f"/items?itemType=annotation&limit=100&start={start}"
        )
        records.extend(batch)
        if len(batch) < 100:
            return records
        start += 100


def parse_pages(pdf_path: Path) -> list[dict]:
    xml = subprocess.check_output(
        ["pdftotext", "-bbox-layout", str(pdf_path), "-"],
        text=True,
        stderr=subprocess.DEVNULL,
    )
    xml = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", xml)
    root = ET.fromstring(xml)
    pages = []
    for page_index, page in enumerate(
        node for node in root.iter() if node.tag.endswith("page")
    ):
        stream = ""
        words = []
        for line_index, line in enumerate(
            node for node in page.iter() if node.tag.endswith("line")
        ):
            for word in (node for node in line if node.tag.endswith("word")):
                token = normalize(word.text or "")
                if not token:
                    continue
                start = len(stream)
                stream += token
                words.append(
                    {
                        "start": start,
                        "end": len(stream),
                        "line": line_index,
                        "xMin": float(word.attrib["xMin"]),
                        "yMin": float(word.attrib["yMin"]),
                        "xMax": float(word.attrib["xMax"]),
                        "yMax": float(word.attrib["yMax"]),
                    }
                )
        pages.append(
            {
                "index": page_index,
                "width": float(page.attrib["width"]),
                "height": float(page.attrib["height"]),
                "stream": stream,
                "words": words,
            }
        )
    return pages


def locate(pages: list[dict], text: str) -> dict:
    needle = normalize(text)
    matches = []
    for page in pages:
        start = page["stream"].find(needle)
        if start >= 0:
            matches.append((page, start))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one exact normalized match; found {len(matches)}: "
            f"{text[:100]}"
        )
    page, start = matches[0]
    end = start + len(needle)
    selected = [
        word
        for word in page["words"]
        if word["start"] < end and word["end"] > start
    ]
    grouped = []
    for word in selected:
        if not grouped or grouped[-1][0]["line"] != word["line"]:
            grouped.append([])
        grouped[-1].append(word)
    rects = [
        [
            round(min(word["xMin"] for word in line), 3),
            round(page["height"] - max(word["yMax"] for word in line), 3),
            round(max(word["xMax"] for word in line), 3),
            round(page["height"] - min(word["yMin"] for word in line), 3),
        ]
        for line in grouped
    ]
    note_y = min(rects[0][1], page["height"] - 24.0)
    return {
        "pageIndex": page["index"],
        "pageLabel": str(page["index"] + 1),
        "rects": rects,
        "noteRect": [
            round(page["width"] - 48.0, 3),
            round(note_y, 3),
            round(page["width"] - 26.0, 3),
            round(note_y + 22.0, 3),
        ],
        "sortIndex": f"{page['index']:05d}|{start:06d}|00000",
        "noteSortIndex": f"{page['index']:05d}|{start:06d}|00001",
    }


def validated_papers(
    manifest_path: Path,
    selected_keys: set[str],
    *,
    allow_existing: bool = False,
) -> list[dict]:
    manifest = json.loads(manifest_path.read_text())
    papers = manifest["papers"]
    if selected_keys:
        known = {paper["parentKey"] for paper in papers}
        missing = sorted(selected_keys - known)
        if missing:
            raise RuntimeError(f"Parent keys absent from manifest: {missing}")
        papers = [paper for paper in papers if paper["parentKey"] in selected_keys]
    annotations = all_annotations()
    annotated_attachments = {
        record["data"].get("parentItem") for record in annotations
    }
    output = []
    for paper in papers:
        parent = api_get(f"/items/{paper['parentKey']}")["data"]
        attachment = api_get(f"/items/{paper['attachmentKey']}")["data"]
        if parent.get("title") != paper["title"]:
            raise RuntimeError(f"Title mismatch for {paper['parentKey']}")
        if attachment.get("parentItem") != paper["parentKey"]:
            raise RuntimeError(f"Attachment mismatch for {paper['title']}")
        if not allow_existing and paper["attachmentKey"] in annotated_attachments:
            raise RuntimeError(f"Attachment already annotated: {paper['title']}")
        pdf_path = Path(paper["pdfPath"])
        if not pdf_path.is_file():
            raise RuntimeError(f"Missing PDF: {pdf_path}")
        pages = parse_pages(pdf_path)
        entries = []
        for number, concept in enumerate(paper["concepts"], start=1):
            if len(concept["text"].split()) < 8:
                raise RuntimeError(f"Highlight too short in {paper['title']}")
            if len(concept["note"].strip()) < 180:
                raise RuntimeError(f"Note too short in {paper['title']}")
            entries.append(
                {
                    "text": concept["text"],
                    "note": f"{number}. {concept['heading']}\n\n{concept['note']}",
                    **locate(pages, concept["text"]),
                }
            )
        output.append({**paper, "entries": entries})
    return output


def annotation_javascript(papers: list[dict]) -> str:
    payload = json.dumps(
        [
            {
                "parentKey": paper["parentKey"],
                "attachmentKey": paper["attachmentKey"],
                "title": paper["title"],
                "entries": paper["entries"],
            }
            for paper in papers
        ],
        ensure_ascii=False,
        indent=2,
    )
    return f"""// Paste into Zotero Tools -> Developer -> Run JavaScript.
const papers = {payload};
const libraryID = Zotero.Libraries.userLibraryID;
const completed = [];
for (const paper of papers) {{
    const parent = Zotero.Items.getByLibraryAndKey(libraryID, paper.parentKey);
    const attachment = Zotero.Items.getByLibraryAndKey(libraryID, paper.attachmentKey);
    if (!parent || !attachment || attachment.parentID !== parent.id) {{
        throw new Error(`Invalid item pair for ${{paper.title}}`);
    }}
    let count = 0;
    for (const entry of paper.entries) {{
        await Zotero.Annotations.saveFromJSON(attachment, {{
            key: Zotero.DataObjectUtilities.generateKey(),
            type: 'highlight', text: entry.text, comment: '', color: '#ffd400',
            pageLabel: entry.pageLabel, sortIndex: entry.sortIndex,
            position: {{pageIndex: entry.pageIndex, rects: entry.rects}}, tags: []
        }});
        await Zotero.Annotations.saveFromJSON(attachment, {{
            key: Zotero.DataObjectUtilities.generateKey(),
            type: 'note', comment: entry.note, color: '#ffd400',
            pageLabel: entry.pageLabel, sortIndex: entry.noteSortIndex,
            position: {{pageIndex: entry.pageIndex, rects: [entry.noteRect]}}, tags: []
        }});
        count += 2;
    }}
    completed.push({{title: paper.title, annotations: count}});
}}
return {{papers: completed.length, completed}};
"""


def tag_javascript(papers: list[dict]) -> str:
    payload = json.dumps(
        [{"key": paper["parentKey"], "title": paper["title"]} for paper in papers],
        ensure_ascii=False,
        indent=2,
    )
    return f"""// Run only after annotation verification.
const papers = {payload};
const libraryID = Zotero.Libraries.userLibraryID;
for (const paper of papers) {{
    const item = Zotero.Items.getByLibraryAndKey(libraryID, paper.key);
    if (!item) throw new Error(`Missing paper ${{paper.title}}`);
    if (!item.hasTag('need to read')) {{
        item.addTag('need to read');
        await item.saveTx();
    }}
}}
return {{tagged: papers.length}};
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--paper", action="append", default=[])
    parser.add_argument("--tags", action="store_true")
    args = parser.parse_args()
    papers = validated_papers(
        args.manifest,
        set(args.paper),
        allow_existing=args.tags,
    )
    if not papers:
        raise RuntimeError("No papers selected")
    print(tag_javascript(papers) if args.tags else annotation_javascript(papers))
    print(
        f"Validated {len(papers)} paper(s), "
        f"{sum(len(paper['entries']) for paper in papers)} highlight/note pairs.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
