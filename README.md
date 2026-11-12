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

The November 12, 2026 snapshot reports **2,660 citations, h-index 20, and i10-index 32**. Since 2021, the corresponding figures are **2,637, 20, and 30**. Both language versions use this snapshot for the selected-paper cards and publication index. [Google Scholar profile](https://scholar.google.com/citations?user=1J061HIAAAAJ&hl=en&cstart=0&pagesize=100&sortby=pubdate) · [Raw snapshot](data/sources/scholar-2026-11-12.json)

Google Scholar lists 82 records. The site displays **79 indexed works** after excluding three standalone supplementary-material records. It retains patents and separately indexed versions, each with its own citation count. LiAuto-MindViT is the only addition since the October 31 snapshot. The preprint first appeared on September 21. [LiAuto-MindViT on arXiv](https://arxiv.org/abs/2609.24337)

The October 31 refresh added 16 research records (including an ICLR 2025 workshop paper) and 3 patents. The former `finetuning2025` entry shares arXiv:2503.10434 with `learningpersonalized2025` and its earlier title is searchable through `alternateTitles`. The October additions included ProbeTQA, HMPO, LIRQuant, MachEmbodied-U0, Information-Time PPO, What Makes an Efficient VLA?, LiSTAR, OccDirector, BrainWAM, RISE-RL, RoadVGGT, OpenSkillRisk, VLAFlow, RGS, and STT-Arena. The homepage highlights LIRQuant, MachEmbodied-U0, and BrainWAM above the selected papers.

Publication details were checked against [ACL Anthology](https://aclanthology.org/2026.emnlp-main.900/) for ProbeTQA, [HMPO](https://aclanthology.org/2026.emnlp-main.885/), and [LIRQuant](https://aclanthology.org/2026.findings-emnlp.1589/); Springer for [LiSTAR](https://link.springer.com/chapter/10.1007/978-3-032-37419-6_8), [OccDirector](https://link.springer.com/chapter/10.1007/978-3-032-37196-6_3), and [StreetForward](https://link.springer.com/chapter/10.1007/978-3-032-37359-5_34); and the linked arXiv records for new preprints. CVF proceedings take precedence over Scholar's preprint labels for LinkVLA and DriveCombo. AD-R1 links to the CVPR Findings 2026 proceedings and is labeled accordingly. ICLR 2026 status was confirmed through the official DriveAgent-R1 proceedings and ReflectDrive paper; Scholar supplies the updated ICRA 2026 venue records. Publisher and arXiv author lists can differ between versions; the displayed author list follows the linked publication version.

`metrics_updated_at`, `papers_updated_at`, and each `citationUpdatedAt` use November 12, 2026. Keep the snapshot date and count scope consistent across `data/publications.json`, both homepages, and both publication pages in future refreshes.

## Add an update

The September 10, 2026 milestone and update cover the OTA 8.6 rollout of distilled Mach VLA 2.0 models to NVIDIA Orin and Thor platforms in existing AD Max vehicles, targeting nearly one million owners. The wording describes a rollout that has begun, rather than a completed fleet-wide update. Sources: [Xiang Li's September 10 video on model distillation, platform adaptation, and rollout](https://www.bilibili.com/video/BV1aXYu6eE3Q/) and [September 10 rollout announcement reported by IT Home](https://www.ithome.com/0/1000/955.htm).

Edit `assets/js/content.js` and add one object to `siteContent.updates`. Each update has one date, an optional URL, and English/Chinese title and summary fields. The homepage automatically shows the latest three; the Updates page shows all entries.

## Milestone sources

The production milestones in both homepages were expanded on October 9, 2026. The project-lead role for Mach VLA 2.0 and the internal name VLA 1.0 were supplied by Kun Zhan. Public sources support the release context:

- **2026.05 — Mach VLA 2.0:** Li Auto distinguishes the [April Beijing Auto Show debut](https://ir.lixiang.com/news-releases/news-release-details/li-auto-inc-april-2026-delivery-update) from the [May 15 official L9 launch](https://ir.lixiang.com/news-releases/news-release-details/li-auto-inc-launches-all-new-li-l9-pioneering-embodied-ai/). The milestone uses May for production delivery. Its [Q1 2026 results](https://ir.lixiang.com/news-releases/news-release-details/li-auto-inc-announces-unaudited-first-quarter-2026-financial/) confirm integrated deployment of the proprietary M100 chip and VLA model. The supplied full-stack scope is also described in [coverage of Livis Day](https://www.leiphone.com/category/transportation/iKKAYzqzrW0294JG.html).
- **2025.08 — VLA 1.0:** The [official i8 announcement](https://www.lixiang.com/news/136.html) is dated July 29 and specifies August 20 deliveries. August refers to first customer deliveries, not the announcement date. [August 29 reporting](https://finance.sina.com.cn/stock/t/2025-08-29/doc-infnrnmf4164850.shtml) identifies the VLA architecture as the industry's first delivered in production vehicles. The first-production claim applies to the driving model, not all VLA research.
- **2024.10 — E2E + VLM:** The [Q3 2024 results](https://ir.lixiang.com/news-releases/news-release-details/li-auto-inc-announces-unaudited-third-quarter-2024-financial) confirm the OTA 6.4 rollout to more than 320,000 AD Max users. The [2024 ESG report](https://ir.lixiang.com/static-files/756c207b-c016-4b5c-94e4-4eef9da91940), page 26, describes the world's first E2E + VLM dual-system architecture, announced in July and fully rolled out in October. The [official i8 announcement](https://www.lixiang.com/news/136.html) also describes Li Auto as the first company to deliver end-to-end advanced assisted driving; the homepage scopes that claim to China. [October 23 coverage](https://www.eeo.com.cn/2024/1023/692871.shtml) supplies the exact rollout date.

The visible milestone links now point to related videos. Titles, upload dates, and descriptions were checked on Bilibili on October 9, 2026:

| Milestone | Video | Publisher / upload date |
| --- | --- | --- |
| 2026.09 | [Mach VLA 2.0 rollout overview](https://www.bilibili.com/video/BV1aXYu6eE3Q/) | Xiang Li / September 10, 2026 |
| 2026.06 | [Livis Day full replay with subtitles](https://www.bilibili.com/video/BV14njP6AEHi/) | 理想TOP2 / June 16, 2026 |
| 2026.05 | [Kun Zhan interview on Mach M100 and L9 Livis](https://www.bilibili.com/video/BV1riLw6nEfe/) | 影总聊智驾 / May 18, 2026 |
| 2025.08 | [Li i8 launch event, full replay](https://www.bilibili.com/video/BV1kh8ozWEKq/) | 德发频道 / July 29, 2025 |
| 2024.10 | [E2E + VLM architecture at the 2024 summer driving event](https://www.bilibili.com/video/BV1A4421U7rW/) | Li Auto / July 5, 2024 |

Video dates describe the related presentation or interview; milestone dates describe the production event. In particular, the July 2025 i8 launch precedes August deliveries, and the July 2024 architecture presentation precedes the October rollout. The previous Livis Day YouTube video (`E8DX3SZcUfA`) showed “removed by the uploader”; its update entries now use the Bilibili replay above. The September rollout update uses the same video as its milestone.

## Update social profiles

Edit these values in `assets/js/content.js`:

```js
weibo: "https://weibo.com/your-profile",
x: "https://x.com/your-handle",
xiaohongshu: "https://xhslink.cn/m/your-profile",
```

Empty values are intentionally hidden from the published site.

## Refresh publications

The original snapshot was imported from the previous site's Scholar data. To import a compatible YAML snapshot:

```bash
python3 scripts/import_publications.py /path/to/scholar.yml data/publications.json
```

This legacy helper requires PyYAML and replaces the JSON file; it does not preserve later manual metadata, source fields, or alternate titles. Review its output before using it for a future refresh. The website itself has no Python or JavaScript package dependency.
