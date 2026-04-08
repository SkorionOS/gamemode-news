#!/usr/bin/env python3
"""
Parse announcements/*.md and generate announcements.json.
Keeps the latest N entries sorted by date descending.
"""

import glob
import json
import os
import sys

MAX_ENTRIES = 20
ANNOUNCEMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "announcements")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "announcements.json")


def parse_front_matter(text):
    """Parse --- delimited front matter and body from a markdown file."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end < 0:
        return {}, text

    meta = {}
    for line in lines[1:end]:
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        meta[key.strip()] = val.strip()

    body = "\n".join(lines[end + 1:]).strip()
    return meta, body


def main():
    md_dir = os.path.normpath(ANNOUNCEMENTS_DIR)
    out_file = os.path.normpath(OUTPUT_FILE)

    pattern = os.path.join(md_dir, "*.md")
    files = sorted(glob.glob(pattern))

    entries = []
    for fpath in files:
        with open(fpath, "r", encoding="utf-8") as f:
            text = f.read()
        meta, body = parse_front_matter(text)
        if not meta.get("title"):
            print(f"SKIP (no title): {fpath}", file=sys.stderr)
            continue
        entries.append({
            "title": meta.get("title", ""),
            "date": meta.get("date", ""),
            "channel": meta.get("channel", ""),
            "lang": meta.get("lang", ""),
            "body": body,
        })

    entries.sort(key=lambda e: e["date"], reverse=True)
    entries = entries[:MAX_ENTRIES]

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Generated {out_file}: {len(entries)} entries from {len(files)} files")


if __name__ == "__main__":
    main()
