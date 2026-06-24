#!/usr/bin/env python3
"""Build the minimal GitHub Pages site for VLM attack results."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import build_review_dashboard as dashboard


NEWSTUFF_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = NEWSTUFF_ROOT.parent
DOCS = REPO_ROOT / "docs"
DOCS_IMAGES = DOCS / "data" / "images_raw" / "normal"
DOCS_INDEX = DOCS / "index.html"
DOCS_NOJEKYLL = DOCS / ".nojekyll"


def copy_if_needed(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size == src.stat().st_size:
        return False
    shutil.copy2(src, dst)
    return True


def main() -> int:
    records = dashboard.make_records()
    copied = 0
    missing: list[str] = []

    for record in records:
        image_path = record["image_path"]
        src = NEWSTUFF_ROOT / image_path
        dst = DOCS / image_path
        if not src.exists():
            missing.append(image_path)
            continue
        if copy_if_needed(src, dst):
            copied += 1
        record["image_src"] = image_path

    if missing:
        print("Missing image files:")
        for path in missing:
            print(f"  {path}")
        return 1

    DOCS.mkdir(parents=True, exist_ok=True)
    DOCS_NOJEKYLL.write_text("", encoding="utf-8")
    DOCS_INDEX.write_text(
        dashboard.HTML_TEMPLATE.replace("__RECORDS_JSON__", json.dumps(records, ensure_ascii=False)),
        encoding="utf-8",
    )
    image_count = len(list(DOCS_IMAGES.glob("*")))
    print(f"Wrote {DOCS_INDEX.relative_to(REPO_ROOT)}")
    print(f"Copied/updated images: {copied}")
    print(f"Deploy image count: {image_count}")
    print(f"Embedded records: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
