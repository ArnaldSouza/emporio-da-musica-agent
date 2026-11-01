"""Store policy manual: text extraction, split by section and the policy lookup tool."""

import re
from pathlib import Path

from pypdf import PdfReader

MANUAL_PATH = Path(__file__).resolve().parent / "data" / "políticas_da_loja.pdf"
PAGE_HEADER = "Empório da Música Manual de Políticas e Procedimentos"
PAGE_FOOTER_PATTERN = re.compile(r"^Página \d+$")
# Assumption: the manual has two e-mail spellings and two WhatsApp numbers; one version is kept
CONTACT_FIXES = {
    "contato@empóriodamusica.com.br": "contato@emporiodamusica.com.br",
    "(67) 3321-4500": "(67) 3341-4444",
}


def extract_manual_lines() -> list[str]:
    """Extract the manual as clean, non-empty lines, without page headers and footers."""
    if not MANUAL_PATH.exists():
        raise FileNotFoundError(f"Policy manual not found: {MANUAL_PATH}")
    reader = PdfReader(MANUAL_PATH)
    # Layout mode keeps one text line per line; the default mode may break lines word by word
    text = "\n".join(page.extract_text(extraction_mode="layout") for page in reader.pages)
    for wrong, right in CONTACT_FIXES.items():
        text = text.replace(wrong, right)
    lines = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())  # collapses the spaces used to align table columns
        if line and line != PAGE_HEADER and not PAGE_FOOTER_PATTERN.match(line):
            lines.append(line)
    return lines


def split_sections(lines: list[str]) -> dict[int, str]:
    """Split the manual lines into its numbered top-level sections, e.g. {2: "2. Horário ..."}.

    Only the next expected number starts a section, so numbered steps inside a
    section (such as the 1-5 service flow in section 7) are not taken as titles.
    """
    sections: dict[int, list[str]] = {}
    current = 0  # lines before section 1 (the cover page) are ignored
    for line in lines:
        if re.match(rf"^{current + 1}\.\s", line):
            current += 1
            sections[current] = []
        if current:
            sections[current].append(line)
    return {number: "\n".join(section_lines) for number, section_lines in sections.items()}