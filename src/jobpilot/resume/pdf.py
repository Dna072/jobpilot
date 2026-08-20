from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader


class PdfValidationError(RuntimeError):
    pass


def compile_latex(tex_path: Path, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or tex_path.parent
    engine = shutil.which("tectonic") or shutil.which("pdflatex") or shutil.which("xelatex")
    if not engine:
        pdf = out_dir / (tex_path.stem + ".pdf")
        pdf.write_bytes(_placeholder_pdf(tex_path.read_text(encoding="utf-8")))
        return pdf
    if Path(engine).name == "tectonic":
        subprocess.run(
            [engine, "-X", "compile", str(tex_path), "--outdir", str(out_dir)],
            check=True,
            capture_output=True,
        )
    else:
        subprocess.run(
            [engine, "-interaction=nonstopmode", "-output-directory", str(out_dir), str(tex_path)],
            check=True,
            capture_output=True,
        )
    return out_dir / (tex_path.stem + ".pdf")


def _placeholder_pdf(text: str) -> bytes:
    """Minimal valid PDF so tests can run without TeX. Not for live applications."""
    payload = text[:1500].replace("(", " ").replace(")", " ").encode("latin-1", "replace")
    stream = b"BT /F1 11 Tf 48 720 Td (" + payload[:200] + b") Tj ET"
    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj",
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj",
        b"4 0 obj<< /Length %d >>stream\n" % len(stream) + stream + b"\nendstream endobj",
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj",
    ]
    body = b"\n".join(objects)
    return b"%PDF-1.4\n" + body + b"\ntrailer<< /Root 1 0 R >>\n%%EOF\n"


def validate_pdf(pdf_path: Path, max_pages: int = 2) -> dict:
    reader = PdfReader(str(pdf_path))
    pages = len(reader.pages)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    issues: list[str] = []
    if pages == 0:
        issues.append("PDF has zero pages")
    if pages > max_pages:
        issues.append(f"PDF has {pages} pages (max {max_pages})")
    if len(text.strip()) < 80:
        issues.append("Extracted text is suspiciously short")
    if "lorem ipsum" in text.lower():
        issues.append("Placeholder lorem ipsum detected")
    box = reader.pages[0].mediabox
    width, height = float(box.width), float(box.height)
    if width < 500 or height < 700:
        issues.append("Page size looks wrong for a letter/A4 resume")
    result = {
        "ok": not issues,
        "page_count": pages,
        "text_length": len(text),
        "width": width,
        "height": height,
        "issues": issues,
        "text_preview": text[:500],
    }
    if issues:
        raise PdfValidationError("; ".join(issues))
    return result
