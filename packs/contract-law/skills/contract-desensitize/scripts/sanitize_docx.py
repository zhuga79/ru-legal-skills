#!/usr/bin/env python3
"""sanitize_docx.py — локальная замена текста в DOCX по mapping JSON.

Usage:
    python sanitize_docx.py --file src.docx --mapping mapping.json --out out.docx

Mapping: {"[ЗАКАЗЧИК]": "ООО Ромашка", ...}
Оригинал не изменяется. Замена идёт в document.xml, headers, footers, footnotes,
comments (текстовые узлы). Не трогает изображения.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
TARGETS = (
    "word/document.xml",
    "word/header1.xml",
    "word/header2.xml",
    "word/footer1.xml",
    "word/footer2.xml",
    "word/footnotes.xml",
    "word/endnotes.xml",
    "word/comments.xml",
)


def replace_in_xml(data: bytes, mapping: dict[str, str]) -> tuple[bytes, int]:
    root = ET.fromstring(data)
    count = 0
    for node in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
        if node.text:
            new = node.text
            for ph, orig in mapping.items():
                if orig and orig in new:
                    new = new.replace(orig, ph)
                    count += 1
            node.text = new
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), count


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--mapping", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
    src = Path(args.file)
    out = Path(args.out)
    if src.resolve() == out.resolve():
        raise SystemExit("out не должен совпадать с источником")

    total = 0
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in TARGETS:
                data, n = replace_in_xml(data, mapping)
                total += n
            zout.writestr(item, data)

    print(f"замен: {total}; записано: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
