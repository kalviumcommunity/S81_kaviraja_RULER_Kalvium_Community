"""
Multi-Format Document Loader for RAG Applications.

Supports parsing PDF, HTML, Markdown, and Plain Text files into a unified
plain-text representation tagged with source metadata and error handling
to survive unreadable, missing, or corrupt files without crashing.
"""

import os
import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

# Import third-party libraries with fallback handling if needed
try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


# Configure module logger
logger = logging.getLogger("DocumentLoader")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] DocumentLoader: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@dataclass
class Document:
    """
    Unified plain-text document representation with source metadata identity.
    """
    source: str
    filename: str
    format: str
    content: str = ""
    char_count: int = 0
    word_count: int = 0
    status: str = "success"  # "success", "error", or "skipped"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def preview(self, max_length: int = 150) -> str:
        """Return a short clean preview sample of the extracted text."""
        if not self.content:
            return "[No Content]"
        cleaned = re.sub(r"\s+", " ", self.content).strip()
        if len(cleaned) <= max_length:
            return cleaned
        return cleaned[:max_length] + "..."

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to a JSON-serializable dictionary."""
        return {
            "source": self.source,
            "filename": self.filename,
            "format": self.format,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "status": self.status,
            "error_message": self.error_message,
            "sample_preview": self.preview(),
            "metadata": self.metadata,
            "content": self.content,
        }


class BaseExtractor:
    """Abstract base class for document format extractors."""
    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        raise NotImplementedError("Subclasses must implement extract()")


class PDFExtractor(BaseExtractor):
    """Extractor for PDF documents using pypdf."""
    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf library is required for PDF parsing.")
        
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            extracted_pages = []
            
            for index, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                extracted_pages.append(page_text.strip())
            
            full_text = "\n\n".join([p for p in extracted_pages if p])
            if not full_text.strip():
                raise ValueError("PDF contains no readable text or is image-only.")

            metadata = {
                "page_count": total_pages,
                "encrypted": reader.is_encrypted,
            }
            return full_text, metadata

        except (PdfReadError, Exception) as e:
            raise ValueError(f"Corrupt or invalid PDF file ({type(e).__name__}): {str(e)}")


class HTMLExtractor(BaseExtractor):
    """Extractor for HTML documents using BeautifulSoup."""
    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        if not BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 library is required for HTML parsing.")

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_html = f.read()

            soup = BeautifulSoup(raw_html, "html.parser")
            
            # Remove non-content tags
            for element in soup(["script", "style", "head", "title", "meta", "[document]"]):
                element.decompose()

            # Extract text lines
            lines = (line.strip() for line in soup.get_text().splitlines())
            # Drop blank lines
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)

            if not text.strip():
                raise ValueError("HTML document yielded empty plain text.")

            title = soup.title.string if soup.title else os.path.basename(file_path)
            metadata = {
                "html_title": title,
                "raw_html_length": len(raw_html),
            }
            return text, metadata

        except Exception as e:
            raise ValueError(f"Failed to parse HTML document ({type(e).__name__}): {str(e)}")


class MarkdownExtractor(BaseExtractor):
    """Extractor for Markdown documents."""
    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Normalize line endings
            cleaned_text = content.replace("\r\n", "\n")
            if not cleaned_text.strip():
                raise ValueError("Markdown file is empty.")

            # Count headers
            headers = re.findall(r"^#{1,6}\s+.+$", cleaned_text, flags=re.MULTILINE)
            metadata = {
                "header_count": len(headers),
                "sections": [h.strip("# ").strip() for h in headers],
            }
            return cleaned_text, metadata

        except Exception as e:
            raise ValueError(f"Failed to read Markdown document ({type(e).__name__}): {str(e)}")


class TextExtractor(BaseExtractor):
    """Extractor for Plain Text (.txt) documents."""
    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Fallback encoding
            with open(file_path, "r", encoding="latin-1", errors="replace") as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read plain text file ({type(e).__name__}): {str(e)}")

        cleaned_text = content.replace("\r\n", "\n")
        if not cleaned_text.strip():
            raise ValueError("Plain text document is empty.")

        metadata = {"lines_count": len(cleaned_text.splitlines())}
        return cleaned_text, metadata


class DocumentLoader:
    """
    Multi-format document loader capable of loading PDF, HTML, Markdown, and TXT files,
    preserving source identity, confirming intake, and handling corrupt/missing files.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf": PDFExtractor(),
        ".html": HTMLExtractor(),
        ".htm": HTMLExtractor(),
        ".md": MarkdownExtractor(),
        ".markdown": MarkdownExtractor(),
        ".txt": TextExtractor(),
    }

    def __init__(self, logger_override: Optional[logging.Logger] = None):
        self.logger = logger_override or logger

    def get_format_from_extension(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".pdf"]:
            return "pdf"
        elif ext in [".html", ".htm"]:
            return "html"
        elif ext in [".md", ".markdown"]:
            return "markdown"
        elif ext in [".txt"]:
            return "txt"
        return ext.lstrip(".") if ext else "unknown"

    def load_document(self, file_path: str) -> Document:
        """
        Load a single document by path. Robust to missing, corrupt, or unsupported files.
        """
        filename = os.path.basename(file_path)
        source_id = file_path.replace("\\", "/")
        doc_format = self.get_format_from_extension(file_path)

        # Task 2: Check missing file
        if not os.path.exists(file_path):
            msg = f"Missing file: Path '{file_path}' does not exist."
            self.logger.warning(f"[SKIPPED] {source_id} -> {msg}")
            return Document(
                source=source_id,
                filename=filename,
                format=doc_format,
                status="skipped",
                error_message=msg,
            )

        ext = os.path.splitext(file_path)[1].lower()
        # Task 2: Check unsupported file extension
        if ext not in self.SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(self.SUPPORTED_EXTENSIONS.keys()))
            msg = f"Unsupported file extension '{ext}'. Supported extensions: [{supported}]."
            self.logger.warning(f"[SKIPPED] {source_id} -> {msg}")
            return Document(
                source=source_id,
                filename=filename,
                format=doc_format,
                status="skipped",
                error_message=msg,
            )

        # Extract content using format extractor
        extractor = self.SUPPORTED_EXTENSIONS[ext]
        try:
            content, metadata = extractor.extract(file_path)
            char_count = len(content)
            word_count = len(content.split())
            
            # File size in bytes
            file_size = os.path.getsize(file_path)
            metadata["file_size_bytes"] = file_size

            self.logger.info(f"[SUCCESS] {source_id} ({doc_format.upper()}) - Loaded {char_count} chars, {word_count} words.")
            
            return Document(
                source=source_id,
                filename=filename,
                format=doc_format,
                content=content,
                char_count=char_count,
                word_count=word_count,
                status="success",
                error_message=None,
                metadata=metadata,
            )

        except Exception as e:
            # Task 2: Handle corrupt / unreadable file gracefully
            err_msg = str(e)
            self.logger.error(f"[ERROR] {source_id} ({doc_format.upper()}) -> {err_msg}")
            return Document(
                source=source_id,
                filename=filename,
                format=doc_format,
                status="error",
                error_message=err_msg,
            )

    def load_batch(self, file_paths: List[str]) -> List[Document]:
        """Load a batch of document file paths."""
        documents = []
        for path in file_paths:
            doc = self.load_document(path)
            documents.append(doc)
        return documents

    def load_directory(self, directory_path: str, recursive: bool = True) -> List[Document]:
        """
        Scan a directory and load all files.
        """
        if not os.path.exists(directory_path):
            self.logger.error(f"Directory not found: {directory_path}")
            return []

        file_paths = []
        if recursive:
            for root, _, files in os.walk(directory_path):
                for f in sorted(files):
                    file_paths.append(os.path.join(root, f))
        else:
            for f in sorted(os.listdir(directory_path)):
                full_p = os.path.join(directory_path, f)
                if os.path.isfile(full_p):
                    file_paths.append(full_p)

        return self.load_batch(file_paths)

    def print_intake_summary(self, documents: List[Document]) -> None:
        """
        Task 4: Print intake confirmation showing text length, status, and sample preview.
        """
        print("\n==================================================================")
        print("                 DOCUMENT INTAKE CONFIRMATION SUMMARY             ")
        print("==================================================================")
        
        success_count = 0
        skipped_count = 0
        error_count = 0
        total_chars = 0

        for idx, doc in enumerate(documents, start=1):
            print(f"\n[{idx}/{len(documents)}] Source ID : {doc.source}")
            print(f"      Filename  : {doc.filename}")
            print(f"      Format    : {doc.format.upper()}")
            print(f"      Status    : {doc.status.upper()}")

            if doc.status == "success":
                success_count += 1
                total_chars += doc.char_count
                print(f"      Text Length: {doc.char_count} chars | {doc.word_count} words")
                print(f"      Sample    : \"{doc.preview(140)}\"")
            else:
                if doc.status == "skipped":
                    skipped_count += 1
                else:
                    error_count += 1
                print(f"      Reason    : {doc.error_message}")
            print("------------------------------------------------------------------")

        print("\n------------------------------------------------------------------")
        print(f"TOTAL DOCUMENTS PROCESSED: {len(documents)}")
        print(f"  - Successfully Loaded  : {success_count}")
        print(f"  - Skipped / Unsupported: {skipped_count}")
        print(f"  - Error / Corrupt      : {error_count}")
        print(f"  - Total Extracted Chars: {total_chars}")
        print("==================================================================\n")


if __name__ == "__main__":
    sample_dir = os.path.join("data", "sample_corpus")
    if not os.path.exists(sample_dir):
        print(f"Sample corpus directory '{sample_dir}' not found. Run scripts/generate_sample_corpus.py first.")
    else:
        loader = DocumentLoader()
        sample_batch = [
            os.path.join(sample_dir, "banking_policy.pdf"),
            os.path.join(sample_dir, "compliance_faq.html"),
            os.path.join(sample_dir, "rag_architecture.md"),
            os.path.join(sample_dir, "system_notes.txt"),
            os.path.join(sample_dir, "corrupt_doc.pdf"),
            os.path.join(sample_dir, "unsupported_doc.docx"),
            os.path.join(sample_dir, "non_existent_file.pdf"),
        ]
        docs = loader.load_batch(sample_batch)
        loader.print_intake_summary(docs)

