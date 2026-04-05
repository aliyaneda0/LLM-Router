from __future__ import annotations

from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent.parent

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT = 42
TOP = 756
BOTTOM = 42


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def add_line(commands: list[str], x: int, y: int, text: str, font: str, size: int) -> None:
    safe_text = escape_pdf_text(text)
    commands.append(f"BT /{font} {size} Tf {x} {y} Td ({safe_text}) Tj ET")


def parse_markdown(md_text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for raw_line in md_text.splitlines():
        line = raw_line.strip()
        if not line:
            blocks.append(("space", ""))
        elif line.startswith("# "):
            blocks.append(("title", line[2:].strip()))
        elif line.startswith("## "):
            blocks.append(("heading", line[3:].strip()))
        elif line.startswith("- "):
            blocks.append(("bullet", line[2:].strip()))
        elif line[:2].isdigit() and ". " in line:
            number, rest = line.split(". ", 1)
            if number.isdigit():
                blocks.append(("numbered", f"{number}. {rest.strip()}"))
            else:
                blocks.append(("body", line))
        else:
            blocks.append(("body", line))
    return blocks


def render_lines(blocks: list[tuple[str, str]]) -> list[tuple[str, int, str, int]]:
    rendered: list[tuple[str, int, str, int]] = []
    for kind, text in blocks:
        if kind == "space":
            rendered.append(("F1", 6, "", 10))
            continue

        if kind == "title":
            rendered.append(("F2", 18, text, 24))
            continue

        if kind == "heading":
            rendered.append(("F2", 11, text.upper(), 14))
            continue

        if kind == "bullet":
            wrapped = textwrap.wrap(text, width=92) or [text]
            for index, part in enumerate(wrapped):
                prefix = "- " if index == 0 else "  "
                rendered.append(("F1", 9, f"{prefix}{part}", 11))
            continue

        if kind == "numbered":
            first, rest = text.split(" ", 1)
            wrapped = textwrap.wrap(rest, width=89) or [rest]
            for index, part in enumerate(wrapped):
                prefix = f"{first} " if index == 0 else "   "
                rendered.append(("F1", 9, f"{prefix}{part}", 11))
            continue

        wrapped = textwrap.wrap(text, width=94) or [text]
        for part in wrapped:
            rendered.append(("F1", 9, part, 11))

    return rendered


def build_pdf(lines: list[tuple[str, int, str, int]]) -> bytes:
    pages: list[bytes] = []
    commands: list[str] = []
    y = TOP

    for font, size, text, leading in lines:
        if y < BOTTOM:
            pages.append("\n".join(commands).encode("latin-1", errors="replace"))
            commands = []
            y = TOP
        if text:
            add_line(commands, LEFT, y, text, font, size)
        y -= leading

    pages.append("\n".join(commands).encode("latin-1", errors="replace"))

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")

    page_count = len(pages)
    kids = " ".join(f"{3 + index * 2} 0 R" for index in range(page_count))
    objects.append(f"<< /Type /Pages /Count {page_count} /Kids [{kids}] >>".encode("latin-1"))

    font_helvetica_obj = 3 + page_count * 2
    font_bold_obj = font_helvetica_obj + 1

    for index, stream in enumerate(pages):
        page_obj = 3 + index * 2
        content_obj = page_obj + 1
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 {font_helvetica_obj} 0 R /F2 {font_bold_obj} 0 R >> >> "
                f"/Contents {content_obj} 0 R >>"
            ).encode("latin-1")
        )
        objects.append(
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream"
        )

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("latin-1")
    )
    return bytes(pdf)


def render_markdown_to_pdf(source_path: Path, output_path: Path) -> None:
    markdown = source_path.read_text(encoding="utf-8")
    blocks = parse_markdown(markdown)
    lines = render_lines(blocks)
    pdf_bytes = build_pdf(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pdf_bytes)
    print(f"Created {output_path}")


def main() -> None:
    render_markdown_to_pdf(
        ROOT / "docs" / "interview_one_pager.md",
        ROOT / "docs" / "llm_router_interview_one_pager.pdf",
    )
    render_markdown_to_pdf(
        ROOT / "docs" / "interview_questions_answers.md",
        ROOT / "docs" / "llm_router_interview_questions_answers.pdf",
    )


if __name__ == "__main__":
    main()
