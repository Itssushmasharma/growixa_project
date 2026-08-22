#!/usr/bin/env python3
"""Export MASTER_TASK_TRACKER.md to CSV.

The tracker is a markdown table, which makes it easy to read in a diff but
fragile to parse: cells routinely contain a literal `|` inside a code span
(`str | None`, `POST/GET | 403`), and a naive split on `|` shifts every field
after it. That is how a task's Status gets misread by anything reading the
tracker programmatically.

This exporter splits on `|` only when it is *outside* a backtick code span, so
those rows survive intact, and emits CSV where quoting handles the delimiter
properly. The markdown table stays the source of truth; the CSV is a generated
view -- regenerate it rather than editing it.

Usage:
    python3 scripts/tracker_to_csv.py            # write the CSV next to the .md
    python3 scripts/tracker_to_csv.py --check    # verify the CSV is up to date
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRACKER_MD = REPO_ROOT / "docs" / "00-project-control" / "MASTER_TASK_TRACKER.md"
TRACKER_CSV = REPO_ROOT / "docs" / "00-project-control" / "MASTER_TASK_TRACKER.csv"


def split_row(line: str) -> list[str]:
    """Split a markdown table row on `|`, ignoring pipes inside code spans."""
    cells: list[str] = []
    buf: list[str] = []
    in_code = False
    for ch in line.strip():
        if ch == "`":
            in_code = not in_code
            buf.append(ch)
        elif ch == "|" and not in_code:
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    cells.append("".join(buf).strip())
    # A well-formed row is wrapped in pipes, producing an empty first and last cell.
    if cells and not cells[0]:
        cells.pop(0)
    if cells and not cells[-1]:
        cells.pop()
    return cells


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(set(c) <= set("-: ") and "-" in c for c in cells)


def parse(md: str) -> tuple[list[str], list[list[str]]]:
    header: list[str] | None = None
    rows: list[list[str]] = []
    for line in md.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = split_row(line)
        if is_separator(cells):
            continue
        if header is None:
            header = cells
            continue
        if len(cells) != len(header):
            # Report rather than silently pad: a wrong column count means a cell
            # is malformed, and quietly aligning it would hide the real defect.
            print(
                f"warning: {cells[0]!r} has {len(cells)} cells, expected {len(header)}",
                file=sys.stderr,
            )
        rows.append(cells)
    if header is None:
        raise SystemExit(f"no markdown table found in {TRACKER_MD}")
    return header, rows


def render(header: list[str], rows: list[list[str]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        # Pad/truncate only at the CSV boundary so every record is rectangular;
        # the warning above already surfaced any row this affects.
        writer.writerow((row + [""] * len(header))[: len(header)])
    return out.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the CSV is missing or stale instead of writing it",
    )
    args = ap.parse_args()

    header, rows = parse(TRACKER_MD.read_text(encoding="utf-8"))
    csv_text = render(header, rows)

    if args.check:
        current = (
            TRACKER_CSV.read_text(encoding="utf-8") if TRACKER_CSV.exists() else None
        )
        if current != csv_text:
            print(
                f"{TRACKER_CSV.relative_to(REPO_ROOT)} is out of date -- "
                "run: python3 scripts/tracker_to_csv.py",
                file=sys.stderr,
            )
            return 1
        print(f"up to date ({len(rows)} tasks)")
        return 0

    TRACKER_CSV.write_text(csv_text, encoding="utf-8")
    print(f"wrote {TRACKER_CSV.relative_to(REPO_ROOT)} ({len(rows)} tasks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
