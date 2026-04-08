# gamemode-news

Announcement source for [gamemode-news-hook](https://github.com/SkorionOS/gamemode-news-hook).

## Adding announcements

Create a Markdown file in `announcements/` with front matter:

```markdown
---
title: System Update
date: 2026-04-07
channel:
lang: schinese
---
**SkorionOS 55-5**

- Kernel 7.0 rc
- Mesa 26.0.4
```

### Front matter fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | yes | Card title displayed in Steam |
| `date` | yes | Date for sorting (YYYY-MM-DD) |
| `channel` | no | OS branch filter: `rel`, `beta`, `preview`. Empty = all channels |
| `lang` | no | Language filter: `schinese`, `english`, etc. Empty = all languages |

### Body

Markdown body is converted to Steam BBCode by the hook. Supported syntax:

- `**bold**` → `[b]bold[/b]`
- `*italic*` → `[i]italic[/i]`
- `~~strike~~` → `[strike]strike[/strike]`
- `# Heading` → `[h1]Heading[/h1]`
- `- list item` → `[list][*] list item[/list]`
- `[text](url)` → `[url=url]text[/url]`

## How it works

A GitHub Actions workflow runs on every push to `announcements/*.md`, executing `.github/scripts/build-announcements.py` to generate `announcements.json` in the repo root.

`gamemode-news-hook` fetches this JSON file via raw URLs (supports mirror sites for better access).

## Forking

Fork this repo to serve your own announcements. Update the `[repo_mirrors]` URLs in `gamemode-news-hook.conf` to point to your fork.
