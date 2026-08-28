"""
Unit tests for the Multi-Format DocumentLoader module.
Tests PDF, HTML, Markdown, TXT loading, error handling for missing/corrupt files, and metadata preservation.
"""

import os
import sys
import unittest

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from document_loader import DocumentLoader, Document


class TestDocumentLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "sample_corpus"))
        cls.loader = DocumentLoader()

        # Generate sample corpus if missing
        if not os.path.exists(cls.corpus_dir):
            import subprocess
            subprocess.run([sys.executable, "scripts/generate_sample_corpus.py"], check=True)

    def test_task1_pdf_loading(self):
        pdf_path = os.path.join(self.corpus_dir, "banking_policy.pdf")
        doc = self.loader.load_document(pdf_path)
        self.assertEqual(doc.status, "success")
        self.assertEqual(doc.format, "pdf")
        self.assertGreater(doc.char_count, 0)
        self.assertIn("Capital Adequacy Ratio", doc.content)

    def test_task1_html_loading(self):
        html_path = os.path.join(self.corpus_dir, "compliance_faq.html")
        doc = self.loader.load_document(html_path)
        self.assertEqual(doc.status, "success")
        self.assertEqual(doc.format, "html")
        self.assertGreater(doc.char_count, 0)
        self.assertIn("Compliance FAQ", doc.content)

    def test_task1_markdown_loading(self):
        md_path = os.path.join(self.corpus_dir, "rag_architecture.md")
        doc = self.loader.load_document(md_path)
        self.assertEqual(doc.status, "success")
        self.assertEqual(doc.format, "markdown")
        self.assertGreater(doc.char_count, 0)
        self.assertIn("RAG Assistant Architecture", doc.content)

    def test_task1_txt_loading(self):
        txt_path = os.path.join(self.corpus_dir, "system_notes.txt")
        doc = self.loader.load_document(txt_path)
        self.assertEqual(doc.status, "success")
        self.assertEqual(doc.format, "txt")
        self.assertGreater(doc.char_count, 0)
        self.assertIn("Operational Status", doc.content)

    def test_task2_missing_file_handling(self):
        missing_path = os.path.join(self.corpus_dir, "non_existent_file_xyz.pdf")
        doc = self.loader.load_document(missing_path)
        self.assertEqual(doc.status, "skipped")
        self.assertIsNotNone(doc.error_message)
        self.assertIn("Missing file", doc.error_message)

    def test_task2_corrupt_file_handling(self):
        corrupt_path = os.path.join(self.corpus_dir, "corrupt_doc.pdf")
        doc = self.loader.load_document(corrupt_path)
        self.assertEqual(doc.status, "error")
        self.assertIsNotNone(doc.error_message)
        self.assertIn("Corrupt or invalid PDF", doc.error_message)

    def test_task2_unsupported_format_handling(self):
        unsupported_path = os.path.join(self.corpus_dir, "unsupported_doc.docx")
        doc = self.loader.load_document(unsupported_path)
        self.assertEqual(doc.status, "skipped")
        self.assertIsNotNone(doc.error_message)
        self.assertIn("Unsupported file extension", doc.error_message)

    def test_task3_source_identity_preservation(self):
        pdf_path = os.path.join(self.corpus_dir, "banking_policy.pdf")
        doc = self.loader.load_document(pdf_path)
        self.assertEqual(doc.filename, "banking_policy.pdf")
        self.assertTrue(doc.source.endswith("banking_policy.pdf"))

    def test_task4_preview_generation(self):
        pdf_path = os.path.join(self.corpus_dir, "banking_policy.pdf")
        doc = self.loader.load_document(pdf_path)
        preview = doc.preview(50)
        self.assertLessEqual(len(preview), 54)  # 50 + '...'


if __name__ == "__main__":
    unittest.main()
