"""Regression tests for verifiable citation attribution."""

import unittest

from src.citation_attribution import NO_SOURCE_FALLBACK, attribute_answer


class TestCitationAttribution(unittest.TestCase):
    def setUp(self):
        self.source = {
            "marker": "[1]",
            "doc_id": "DOC_BRCF_2026_001",
            "filename": "sample_banking_regulation.txt",
            "source_path": "data/sample_banking_regulation.txt",
            "section": "Section 2: Capital Adequacy",
            "page_number": 2,
            "chunk_id": "DOC_BRCF_2026_001#chunk_002",
            "chunk_index": 1,
            "start_char": 100,
            "end_char": 180,
            "raw_text": "Tier 1 Common Equity Ratio must be not less than 10.5%.",
        }

    def test_valid_marker_maps_to_original_retrieved_text(self):
        result = attribute_answer("The ratio is 10.5% [1].", [self.source])

        self.assertTrue(result["is_grounded"])
        self.assertEqual(result["citation_status"], "VERIFIED")
        citation = result["citations"][0]
        self.assertEqual(citation["chunk_id"], self.source["chunk_id"])
        self.assertEqual(citation["original_retrieved_text"], self.source["raw_text"])
        self.assertEqual(citation["verification"]["status"], "VERIFIED_AGAINST_RETRIEVED_CHUNK")

    def test_missing_marker_returns_no_source_fallback(self):
        result = attribute_answer("The ratio is 10.5%.", [self.source])

        self.assertFalse(result["is_grounded"])
        self.assertEqual(result["answer"], NO_SOURCE_FALLBACK)
        self.assertEqual(result["citations"], [])

    def test_unknown_marker_is_rejected(self):
        result = attribute_answer("The ratio is 10.5% [9].", [self.source])

        self.assertFalse(result["is_grounded"])
        self.assertEqual(result["invalid_citations"], ["[9]"])


if __name__ == "__main__":
    unittest.main()
