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

## Homepage principles

The `#principles` section in both homepages contains eight personal principles for the age of AI, after About and before Milestones. The Chinese copy preserves the supplied essay; the English page contains a translation. Each principle uses native `<details>` / `<summary>` markup, so it can be expanded with a mouse or keyboard without JavaScript. The first principle is open by default.

## Update research metrics

The homepage metrics are static HTML so they remain visible without JavaScript. Update both `index.html` and `zh/index.html`, as well as the `profile` object in `data/publications.json`, when refreshing the figures.

The September 5, 2026 update uses the supplied Google Scholar screenshot: 2,217 citations, h-index 19, and i10-index 28 overall; 2,195, 19, and 26 respectively since 2021. `metrics_updated_at` records this site update, not the screenshot capture date. The publication count, list, and individual citation counts remain from the July 22, 2026 snapshot (`papers_updated_at`); they were not re-fetched. Keep these dates distinct in the homepage source note and on the publication pages.

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
