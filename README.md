# gamemode-news

Announcement source for [gamemode-news-hook](https://github.com/SkorionOS/gamemode-news-hook).

## Adding announcements

Create a Markdown file in `announcements/` with front matter:

```markdown
---
title: System Update
date: 2026-04-07 14:00
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
| `date` | no | Publish time. `YYYY-MM-DD HH:MM`, `YYYY-MM-DD` (auto-appends 00:00), or omit (uses CI build time). Interpreted as Asia/Shanghai timezone |
| `channel` | no | OS branch filter: `rel`, `beta`, `preview`. Empty = all channels |
| `lang` | no | Language filter: `schinese`, `english`, etc. Empty = all languages. If no announcement matches the user's language, English announcements are shown as fallback |

### Body

Markdown body is converted to Steam BBCode by CI. Supported syntax:

- `**bold**` → `[b]bold[/b]`
- `*italic*` → `[i]italic[/i]`
- `~~strike~~` → `[strike]strike[/strike]`
- `# Heading` → `[h1]Heading[/h1]`
- `- list item` → `[list][*] list item[/list]`
- `[text](url)` → `[url=url]text[/url]`

## Web page

CI also generates a static announcement page at `docs/index.html`. View it directly via raw URL from any mirror:

- [GitHub Pages](https://skorionos.github.io/gamemode-news/) (if enabled)
- [Gitee](https://gitee.com/honjow/gamemode-news/raw/main/docs/index.html)
- [Gitea](https://gitea.switchsystem.eu.org/honjow/gamemode-news/raw/branch/main/docs/index.html)
- [GitHub Raw](https://raw.githubusercontent.com/SkorionOS/gamemode-news/master/docs/index.html)

The page auto-detects browser language, supports channel filtering (Stable / Beta / Preview), and works as a single self-contained HTML file with no external dependencies.

## How it works

A GitHub Actions workflow runs on every push to `announcements/*.md`, executing `.github/scripts/build-announcements.py` to generate `announcements.json` and `docs/index.html`. The JSON includes BBCode-converted body and Unix timestamps; the HTML embeds the same data for standalone viewing.

`gamemode-news-hook` fetches this JSON via raw URLs at injection time, and refreshes asynchronously when the user navigates in Steam.

## Forking

Fork this repo to serve your own announcements. Update the `[repo_mirrors]` URLs in `gamemode-news-hook.conf` to point to your fork.
