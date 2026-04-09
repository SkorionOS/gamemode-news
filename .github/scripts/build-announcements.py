#!/usr/bin/env python3
"""
Parse announcements/*.md and generate announcements.json + docs/index.html.
Keeps the latest N entries sorted by date descending.
"""

import glob
import html
import json
import os
import re
import sys
from datetime import datetime

MAX_ENTRIES = 20
ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
ANNOUNCEMENTS_DIR = os.path.join(ROOT_DIR, "announcements")
OUTPUT_FILE = os.path.join(ROOT_DIR, "announcements.json")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
HTML_FILE = os.path.join(DOCS_DIR, "index.html")


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


def md_to_html(text):
    """Convert basic Markdown to HTML."""
    lines = text.split("\n")
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()

        if re.match(r"^[-*]\s+", stripped):
            item = re.sub(r"^[-*]\s+", "", stripped)
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append(f"<li>{html.escape(item)}</li>")
            continue
        elif in_list:
            result.append("</ul>")
            in_list = False

        m = re.match(r"^(#{1,3})\s+(.*)", stripped)
        if m:
            level = len(m.group(1))
            result.append(f"<h{level}>{html.escape(m.group(2))}</h{level}>")
            continue

        if stripped:
            result.append(f"<p>{html.escape(stripped)}</p>")
        else:
            result.append("")

    if in_list:
        result.append("</ul>")

    text = "\n".join(result)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )
    # unescape bold/italic/link text that was escaped inside <p>/<li>
    text = re.sub(r"&lt;(/?(?:strong|em|del|a|ul|li|h[1-3])(?:\s[^>]*)?)&gt;", r"<\1>", text)
    return text


def git_commit_time(filepath):
    """Return the last git commit datetime for a file, or None."""
    import subprocess
    try:
        ts = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "--", filepath],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        if ts:
            return datetime.fromtimestamp(int(ts))
    except Exception:
        pass
    return None


def normalize_date(raw, filepath=None):
    """Fill missing/partial date and return (datetime_str, unix_timestamp).
    No date → git commit time of the file → current time as last resort."""
    if not raw:
        dt = (filepath and git_commit_time(filepath)) or datetime.now()
    elif re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        dt = datetime.strptime(raw, "%Y-%m-%d")
    elif re.match(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}$", raw):
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
    elif re.match(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$", raw):
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    else:
        dt = (filepath and git_commit_time(filepath)) or datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M"), int(dt.timestamp())


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
        date_str, timestamp = normalize_date(meta.get("date", ""), fpath)
        entries.append({
            "title": meta.get("title", ""),
            "date": date_str,
            "timestamp": timestamp,
            "channel": meta.get("channel", ""),
            "lang": meta.get("lang", ""),
            "body": body,
            "bbcode_body": md_to_bbcode(body),
            "html_body": md_to_html(body),
        })

    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    entries = entries[:MAX_ENTRIES]

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Generated {out_file}: {len(entries)} entries from {len(files)} files")

    generate_html(entries)
    print(f"Generated {HTML_FILE}")


def generate_html(entries):
    """Build a static HTML page from announcement entries."""
    os.makedirs(DOCS_DIR, exist_ok=True)

    # Collect available languages and channels from data
    langs = sorted({e["lang"] for e in entries if e["lang"]})
    channels = []
    seen_ch = set()
    for e in entries:
        ch = e["channel"]
        if ch and ch not in seen_ch:
            seen_ch.add(ch)
            channels.append(ch)

    data_json = json.dumps(entries, ensure_ascii=False)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(_html_template(data_json, langs, channels))


CHANNEL_LABELS = {
    "rel": {"en": "Stable", "zh": "稳定版"},
    "beta": {"en": "Beta", "zh": "测试版"},
    "preview": {"en": "Preview", "zh": "预览版"},
    "main": {"en": "Preview", "zh": "前瞻版"},
}

CHANNEL_COLORS = {
    "rel": "#4caf50",
    "beta": "#ff9800",
    "preview": "#f44336",
    "main": "#e40336",
}

LANG_LABELS = {
    "schinese": "简体中文",
    "tchinese": "繁體中文",
    "english": "English",
    "japanese": "日本語",
    "koreana": "한국어",
}


def _html_template(data_json, langs, channels):
    # Build channel tab HTML
    channel_tabs = ""
    for ch in channels:
        label_en = CHANNEL_LABELS.get(ch, {}).get("en", ch)
        label_zh = CHANNEL_LABELS.get(ch, {}).get("zh", ch)
        color = CHANNEL_COLORS.get(ch, "#9e9e9e")
        channel_tabs += (
            f'<button class="tab" data-channel="{ch}" '
            f'data-label-en="{label_en}" data-label-zh="{label_zh}" '
            f'style="--ch-color:{color}">{label_zh}</button>\n'
        )

    # Build language option HTML
    lang_options = ""
    for lang in langs:
        label = LANG_LABELS.get(lang, lang)
        lang_options += f'<option value="{lang}">{label}</option>\n'

    return f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SkorionOS Updates</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0f1923;color:#c7d5e0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.6;min-height:100vh}}
.container{{max-width:720px;margin:0 auto;padding:24px 16px}}
header{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:24px}}
h1{{font-size:1.5rem;color:#fff;font-weight:700;letter-spacing:.5px}}
.lang-select{{background:#1b2838;color:#c7d5e0;border:1px solid #2a475e;border-radius:6px;padding:6px 10px;font-size:.85rem;cursor:pointer}}
.lang-select:focus{{outline:none;border-color:#66c0f4}}
.tabs{{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}}
.tab{{background:transparent;color:#8f98a0;border:1px solid #2a475e;border-radius:20px;padding:6px 16px;font-size:.85rem;cursor:pointer;transition:all .2s}}
.tab:hover{{border-color:#66c0f4;color:#c7d5e0}}
.tab.active{{background:var(--ch-color,#66c0f4);color:#fff;border-color:var(--ch-color,#66c0f4)}}
.tab[data-channel="all"]{{--ch-color:#66c0f4}}
.cards{{display:flex;flex-direction:column;gap:16px}}
.card{{background:#1b2838;border:1px solid #2a475e;border-radius:10px;padding:20px;transition:border-color .2s}}
.card:hover{{border-color:#66c0f4}}
.card-header{{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}}
.card-title{{font-size:1.1rem;color:#fff;font-weight:600}}
.badge{{font-size:.75rem;padding:2px 10px;border-radius:10px;color:#fff;font-weight:500;white-space:nowrap}}
.card-date{{font-size:.8rem;color:#8f98a0;margin-left:auto}}
.card-body{{color:#acb2b8;font-size:.9rem}}
.card-body strong{{color:#c7d5e0}}
.card-body ul{{padding-left:20px;margin:6px 0}}
.card-body li{{margin:3px 0}}
.card-body p{{margin:6px 0}}
.card-body a{{color:#66c0f4;text-decoration:none}}
.card-body a:hover{{text-decoration:underline}}
.empty{{text-align:center;color:#8f98a0;padding:40px 0;font-size:.95rem}}
footer{{text-align:center;color:#4a5568;font-size:.75rem;margin-top:40px;padding:20px 0;border-top:1px solid #1b2838}}
</style>
</head>
<body>
<div class="container">
<header>
  <h1>SkorionOS Updates</h1>
  <select class="lang-select" id="langSelect">
    <option value="all" data-label-en="All Languages" data-label-zh="所有语言">所有语言</option>
    {lang_options}
  </select>
</header>
<div class="tabs" id="tabs">
  <button class="tab active" data-channel="all" data-label-en="All" data-label-zh="全部" style="--ch-color:#66c0f4">全部</button>
  {channel_tabs}
</div>
<div class="cards" id="cards"></div>
<div class="empty" id="empty" style="display:none">No announcements / 暂无公告</div>
<footer>SkorionOS &copy; 2026</footer>
</div>
<script>
var DATA={data_json};
var CHANNEL_LABELS={json.dumps(CHANNEL_LABELS, ensure_ascii=False)};
var LANG_LABELS={json.dumps(LANG_LABELS, ensure_ascii=False)};
var BROWSER_LANG_MAP={{
  "zh":"schinese","zh-cn":"schinese","zh-hans":"schinese",
  "zh-tw":"tchinese","zh-hk":"tchinese","zh-hant":"tchinese",
  "en":"english","ja":"japanese","ko":"koreana",
  "de":"german","fr":"french","es":"spanish","pt":"portuguese",
  "pt-br":"brazilian","ru":"russian","it":"italian","nl":"dutch",
  "pl":"polish","tr":"turkish","vi":"vietnamese","th":"thai",
  "sv":"swedish","fi":"finnish","da":"danish","nb":"norwegian","no":"norwegian",
  "hu":"hungarian","cs":"czech","ro":"romanian","bg":"bulgarian",
  "el":"greek","uk":"ukrainian","id":"indonesian","ms":"indonesian"
}};
var AVAILABLE_LANGS={{}};
for(var i=0;i<DATA.length;i++) if(DATA[i].lang) AVAILABLE_LANGS[DATA[i].lang]=1;

function detectLang(){{
  var langs=navigator.languages||[navigator.language||""];
  for(var i=0;i<langs.length;i++){{
    var tag=langs[i].toLowerCase();
    var match=BROWSER_LANG_MAP[tag]||BROWSER_LANG_MAP[tag.split("-")[0]];
    if(match&&AVAILABLE_LANGS[match]) return match;
  }}
  return "all";
}}

var curChannel="all",curLang=detectLang();
document.getElementById("langSelect").value=curLang;

function render(){{
  var cards=document.getElementById("cards");
  cards.innerHTML="";
  var count=0;
  for(var i=0;i<DATA.length;i++){{
    var e=DATA[i];
    if(curChannel!=="all"&&e.channel!==curChannel) continue;
    if(curLang!=="all"&&e.lang&&e.lang!==curLang) continue;
    count++;
    var ch=e.channel||"";
    var labels=CHANNEL_LABELS[ch]||{{}};
    var labelText=labels.zh||labels.en||ch;
    var color={json.dumps(CHANNEL_COLORS)};
    var c=document.createElement("div");
    c.className="card";
    c.innerHTML='<div class="card-header">'
      +'<span class="card-title">'+esc(e.title)+'</span>'
      +(ch?'<span class="badge" style="background:'+(color[ch]||"#9e9e9e")+'">'+esc(labelText)+'</span>':'')
      +'<span class="card-date">'+esc(e.date.split(" ")[0])+'</span>'
      +'</div>'
      +'<div class="card-body">'+e.html_body+'</div>';
    cards.appendChild(c);
  }}
  document.getElementById("empty").style.display=count?"none":"block";
}}

function esc(s){{var d=document.createElement("span");d.textContent=s;return d.innerHTML;}}

document.getElementById("tabs").addEventListener("click",function(ev){{
  var btn=ev.target.closest(".tab");
  if(!btn) return;
  curChannel=btn.dataset.channel;
  document.querySelectorAll(".tab").forEach(function(t){{t.classList.remove("active")}});
  btn.classList.add("active");
  render();
}});

document.getElementById("langSelect").addEventListener("change",function(){{
  curLang=this.value;
  render();
}});

render();
</script>
</body>
</html>'''


if __name__ == "__main__":
    main()
