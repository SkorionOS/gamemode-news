#!/usr/bin/env python3
"""
Parse announcements/*.md and generate announcements.json.
Keeps the latest N entries sorted by date descending.
"""

import glob
import json
import os
import re
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


def md_to_bbcode(text):
    """Convert basic Markdown to Steam BBCode."""
    lines = text.split("\n")
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()

        if re.match(r"^[-*]\s+", stripped):
            item = re.sub(r"^[-*]\s+", "", stripped)
            if not in_list:
                result.append("[list]")
                in_list = True
            result.append(f"[*] {item}")
            continue
        elif in_list:
            result.append("[/list]")
            in_list = False

        m = re.match(r"^(#{1,3})\s+(.*)", stripped)
        if m:
            level = len(m.group(1))
            tag = f"h{level}"
            result.append(f"[{tag}]{m.group(2)}[/{tag}]")
            continue

        result.append(stripped)

    if in_list:
        result.append("[/list]")

    text = "\n".join(result)
    text = re.sub(r"\*\*(.+?)\*\*", r"[b]\1[/b]", text)
    text = re.sub(r"\*(.+?)\*", r"[i]\1[/i]", text)
    text = re.sub(r"~~(.+?)~~", r"[strike]\1[/strike]", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"[url=\2]\1[/url]", text)
    return text


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
            "bbcode_body": md_to_bbcode(body),
        })

    entries.sort(key=lambda e: e["date"], reverse=True)
    entries = entries[:MAX_ENTRIES]

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Generated {out_file}: {len(entries)} entries from {len(files)} files")


if __name__ == "__main__":
    main()
