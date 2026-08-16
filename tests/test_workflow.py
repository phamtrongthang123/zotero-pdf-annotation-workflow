from __future__ import annotations

import unittest
from unittest import mock

import annotate_from_manual_manifest as writer
import audit_manifest as audit


class WriterTests(unittest.TestCase):
    def test_normalize_ignores_case_punctuation_and_accents(self) -> None:
        self.assertEqual(writer.normalize("Gáze—Model!"), "gazemodel")

    def test_locate_returns_page_and_line_rectangles(self) -> None:
        page = {
            "index": 2,
            "width": 200.0,
            "height": 300.0,
            "stream": "helloworld",
            "words": [
                {
                    "start": 0,
                    "end": 5,
                    "line": 0,
                    "xMin": 10.0,
                    "yMin": 20.0,
                    "xMax": 30.0,
                    "yMax": 30.0,
                },
                {
                    "start": 5,
                    "end": 10,
                    "line": 1,
                    "xMin": 10.0,
                    "yMin": 40.0,
                    "xMax": 35.0,
                    "yMax": 50.0,
                },
            ],
        }
        result = writer.locate([page], "Hello, world!")
        self.assertEqual(result["pageIndex"], 2)
        self.assertEqual(result["pageLabel"], "3")
        self.assertEqual(len(result["rects"]), 2)

    def test_locate_rejects_non_unique_text(self) -> None:
        page = {
            "index": 0,
            "width": 100.0,
            "height": 100.0,
            "stream": "same",
            "words": [],
        }
        with self.assertRaisesRegex(RuntimeError, "found 2"):
            writer.locate([page, page], "same")


class AuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.paper = {
            "parentKey": "PARENT01",
            "attachmentKey": "PDFATT01",
            "title": "Test Paper",
            "concepts": [
                {
                    "heading": "Khái niệm",
                    "text": "An exact complete sentence from the paper.",
                    "note": "Giải thích dễ hiểu.",
                }
            ],
        }
        self.api_records = {
            "/items/PARENT01": {
                "data": {
                    "title": "Test Paper",
                    "tags": [{"tag": "need to read"}],
                }
            },
            "/items/PDFATT01": {"data": {"parentItem": "PARENT01"}},
        }
        self.annotations = [
            {
                "key": "HIGH0001",
                "data": {
                    "parentItem": "PDFATT01",
                    "annotationType": "highlight",
                    "annotationText": "An exact complete sentence from the paper.",
                    "tags": [],
                },
            },
            {
                "key": "NOTE0001",
                "data": {
                    "parentItem": "PDFATT01",
                    "annotationType": "note",
                    "annotationComment": "1. Khái niệm\n\nGiải thích dễ hiểu.",
                    "tags": [],
                },
            },
        ]

    def test_exact_manifest_pair_passes(self) -> None:
        with mock.patch.object(
            audit, "api_get", side_effect=lambda path: self.api_records[path]
        ):
            result = audit.audit_paper(
                self.paper, self.annotations, "need to read"
            )
        self.assertTrue(result["ok"], result["errors"])

    def test_changed_highlight_fails(self) -> None:
        self.annotations[0]["data"]["annotationText"] = "Wrong text"
        with mock.patch.object(
            audit, "api_get", side_effect=lambda path: self.api_records[path]
        ):
            result = audit.audit_paper(
                self.paper, self.annotations, "need to read"
            )
        self.assertFalse(result["ok"])
        self.assertIn(
            "exact highlight text multiset differs from manifest",
            result["errors"],
        )


if __name__ == "__main__":
    unittest.main()
