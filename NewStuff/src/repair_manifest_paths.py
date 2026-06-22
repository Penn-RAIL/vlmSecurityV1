#!/usr/bin/env python3
"""Repair manifest image paths after the final image-folder consolidation."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SAMPLED_IMAGES = DATA / "sampled_images.csv"
FINAL_SAMPLE = DATA / "final_sample_100.csv"
EXTRA_CANDIDATES = DATA / "extra_candidates_20.csv"

PATH_COLUMNS = {
    "source_image",
    "source_path",
    "raw_path",
    "image_label_attack_path",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ensure_column(fieldnames: list[str], column: str) -> list[str]:
    if column not in fieldnames:
        fieldnames.append(column)
    return fieldnames


def validate_paths(path: Path, rows: list[dict[str, str]]) -> list[str]:
    missing: list[str] = []
    for row in rows:
        row_id = row.get("sample_id", "<unknown>")
        for column in PATH_COLUMNS.intersection(row):
            value = row.get(column, "").strip()
            if value and not (ROOT / value).exists():
                missing.append(f"{path.name}:{row_id}:{column}:{value}")
    return missing


def main() -> int:
    sampled_fields, sampled_rows = read_csv(SAMPLED_IMAGES)
    current_by_id = {row["sample_id"]: row for row in sampled_rows}

    for row in sampled_rows:
        row["source_path"] = row["raw_path"]
    write_csv(SAMPLED_IMAGES, sampled_fields, sampled_rows)

    final_fields, final_rows = read_csv(FINAL_SAMPLE)
    final_fields = ensure_column(final_fields, "current_experiment_status")
    for row in final_rows:
        current = current_by_id.get(row["sample_id"])
        if current:
            row["source_image"] = current["raw_path"]
            row["current_experiment_status"] = "retained_in_current_experiment"
        else:
            row["source_image"] = ""
            row["current_experiment_status"] = "replaced_before_final_run"
    write_csv(FINAL_SAMPLE, final_fields, final_rows)

    extra_fields, extra_rows = read_csv(EXTRA_CANDIDATES)
    extra_fields = ensure_column(extra_fields, "current_experiment_status")
    for row in extra_rows:
        current = current_by_id.get(row["sample_id"])
        if current:
            row["source_image"] = current["raw_path"]
            row["current_experiment_status"] = "used_as_replacement"
        else:
            row["source_image"] = ""
            row["current_experiment_status"] = "not_used_in_current_experiment"
    write_csv(EXTRA_CANDIDATES, extra_fields, extra_rows)

    failures = []
    for manifest in (SAMPLED_IMAGES, FINAL_SAMPLE, EXTRA_CANDIDATES):
        _, rows = read_csv(manifest)
        failures.extend(validate_paths(manifest, rows))

    print(f"Updated {SAMPLED_IMAGES.relative_to(ROOT)} rows: {len(sampled_rows)}")
    print(f"Updated {FINAL_SAMPLE.relative_to(ROOT)} rows: {len(final_rows)}")
    print(f"Updated {EXTRA_CANDIDATES.relative_to(ROOT)} rows: {len(extra_rows)}")
    if failures:
        print("Missing non-empty path references:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("All non-empty manifest path references are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
