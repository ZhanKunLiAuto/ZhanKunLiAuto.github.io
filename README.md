# Kun Zhan — Homepage v2

A lightweight bilingual personal website built with semantic HTML, modern CSS, and a small amount of vanilla JavaScript. There is no framework, package install, or build step.

## Local preview

Run a local static server from this directory:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080/`.

## Content map

- `index.html` — English homepage
- `zh/index.html` — Chinese homepage
- `publications/` and `zh/publications/` — complete publication index
- `updates/` and `zh/updates/` — short-form updates, announcements, and current work
- `assets/js/content.js` — social links and update entries
- `data/publications.json` — publication snapshot
- `assets/img/` — portrait, paper previews, and social preview image

## Add an update

Edit `assets/js/content.js` and add one object to `siteContent.updates`. Each update has one date, an optional URL, and English/Chinese title and summary fields. The homepage automatically shows the latest three; the Updates page shows all entries.

## Update social profiles

Edit these values in `assets/js/content.js`:

```js
weibo: "https://weibo.com/your-profile",
x: "https://x.com/your-handle",
xiaohongshu: "https://xhslink.cn/m/your-profile",
```

Empty values are intentionally hidden from the published site.

## Refresh publications

The current snapshot was imported from the previous site's Scholar data. To import a newer compatible YAML snapshot:

```bash
python3 scripts/import_publications.py /path/to/scholar.yml data/publications.json
```

This helper requires PyYAML. The website itself has no Python or JavaScript package dependency.
