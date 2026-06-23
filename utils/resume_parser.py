"""Extract text from an uploaded resume (PDF or DOCX)."""
import os
import PyPDF2


class ParseError(Exception):
    """Raised when a resume file can't be read or parsed."""
    pass


def extract_text(filepath):
    """Extract raw text from a resume file. Supports .pdf and .docx."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return _extract_pdf(filepath)
    elif ext == ".docx":
        return _extract_docx(filepath)
    else:
        raise ParseError(f"Unsupported file type: {ext}")


def _extract_pdf(filepath):
    text = ""
    try:
        with open(filepath, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            if reader.is_encrypted:
                raise ParseError("This PDF is password-protected. Please upload an unlocked file.")
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(f"Could not read PDF: {exc}") from exc

    text = text.strip()
    if not text:
        raise ParseError(
            "No readable text found in this PDF. It may be a scanned image — "
            "try uploading a text-based PDF instead."
        )
    return text


def _extract_docx(filepath):
    try:
        import docx
    except ImportError as exc:
        raise ParseError("DOCX support is not installed on the server.") from exc

    try:
        document = docx.Document(filepath)
        paragraphs = [p.text for p in document.paragraphs]
        text = "\n".join(paragraphs).strip()
    except Exception as exc:
        raise ParseError(f"Could not read DOCX: {exc}") from exc

    if not text:
        raise ParseError("No readable text found in this document.")
    return text
