#!/usr/bin/env python3
"""Audit manifest-driven Zotero annotations through the local read-only API."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path


LOCAL_API = "http://127.0.0.1:23119/api/users/0"


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


def expected_note(number: int, concept: dict) -> str:
    return f"{number}. {concept['heading']}\n\n{concept['note']}"


def audit_paper(
    paper: dict,
    annotations: list[dict],
    required_tag: str | None,
) -> dict:
    parent_record = api_get(f"/items/{paper['parentKey']}")
    attachment_record = api_get(f"/items/{paper['attachmentKey']}")
    parent = parent_record["data"]
    attachment = attachment_record["data"]
    errors: list[str] = []

    if parent.get("title") != paper["title"]:
        errors.append("parent title differs from manifest")
    if attachment.get("parentItem") != paper["parentKey"]:
        errors.append("attachment is not a child of the manifest parent")

    actual = [
        item
        for item in annotations
        if item.get("data", {}).get("parentItem") == paper["attachmentKey"]
    ]
    kinds = Counter(item["data"].get("annotationType") for item in actual)
    expected_count = len(paper["concepts"])
    if kinds["highlight"] != expected_count:
        errors.append(
            f"expected {expected_count} highlights, found {kinds['highlight']}"
        )
    if kinds["note"] != expected_count:
        errors.append(f"expected {expected_count} notes, found {kinds['note']}")
    unexpected_kinds = {
        kind: count
        for kind, count in kinds.items()
        if kind not in {"highlight", "note"}
    }
    if unexpected_kinds:
        errors.append(f"unexpected annotation types: {unexpected_kinds}")

    expected_highlights = Counter(c["text"] for c in paper["concepts"])
    actual_highlights = Counter(
        item["data"].get("annotationText", "")
        for item in actual
        if item["data"].get("annotationType") == "highlight"
    )
    if actual_highlights != expected_highlights:
        errors.append("exact highlight text multiset differs from manifest")

    expected_notes = Counter(
        expected_note(number, concept)
        for number, concept in enumerate(paper["concepts"], start=1)
    )
    actual_notes = Counter(
        item["data"].get("annotationComment", "")
        for item in actual
        if item["data"].get("annotationType") == "note"
    )
    if actual_notes != expected_notes:
        errors.append("exact note text multiset differs from manifest")

    blank_keys = [
        item["key"]
        for item in actual
        if not (
            item["data"].get("annotationText")
            or item["data"].get("annotationComment")
        )
    ]
    if blank_keys:
        errors.append(f"blank annotations: {blank_keys}")

    tagged_keys = [
        item["key"] for item in actual if item["data"].get("tags")
    ]
    if tagged_keys:
        errors.append(f"annotation objects carry tags: {tagged_keys}")

    parent_tags = [tag["tag"] for tag in parent.get("tags", [])]
    if required_tag and required_tag not in parent_tags:
        errors.append(f"parent lacks required tag: {required_tag}")

    return {
        "parentKey": paper["parentKey"],
        "attachmentKey": paper["attachmentKey"],
        "title": paper["title"],
        "expectedPairs": expected_count,
        "actualCounts": dict(kinds),
        "parentTags": parent_tags,
        "ok": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--paper", action="append", default=[])
    parser.add_argument("--require-parent-tag")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    papers = manifest["papers"]
    selected = set(args.paper)
    if selected:
        known = {paper["parentKey"] for paper in papers}
        missing = sorted(selected - known)
        if missing:
            raise RuntimeError(f"Parent keys absent from manifest: {missing}")
        papers = [paper for paper in papers if paper["parentKey"] in selected]
    if not papers:
        raise RuntimeError("No papers selected")

    annotations = all_annotations()
    results = [
        audit_paper(paper, annotations, args.require_parent_tag)
        for paper in papers
    ]
    report = {
        "manifest": str(args.manifest.resolve()),
        "papers": len(results),
        "expectedPairs": sum(row["expectedPairs"] for row in results),
        "passed": sum(row["ok"] for row in results),
        "failed": sum(not row["ok"] for row in results),
        "results": results,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"Audited {report['papers']} paper(s), "
            f"{report['expectedPairs']} expected pair(s): "
            f"{report['passed']} passed, {report['failed']} failed."
        )
        for row in results:
            status = "PASS" if row["ok"] else "FAIL"
            print(f"[{status}] {row['parentKey']} {row['title']}")
            for error in row["errors"]:
                print(f"  - {error}")

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
