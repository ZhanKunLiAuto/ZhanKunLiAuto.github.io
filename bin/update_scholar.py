#!/usr/bin/env python3
import requests
import yaml
import re
from pathlib import Path

DATA_FILE = Path('_data/socials.yml')
BIB_FILE = Path('_bibliography/papers.bib')

BASE_URL = 'https://r.jina.ai/https://scholar.google.com/citations?user={id}&hl=en&cstart=0&pagesize=100'


def read_scholar_id():
    with open(DATA_FILE) as f:
        data = yaml.safe_load(f)
    return data.get('scholar_userid')


def fetch_page(scholar_id):
    url = BASE_URL.format(id=scholar_id)
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text


def parse_publications(text):
    lines = [l.strip() for l in text.splitlines()]
    try:
        start = lines.index('Markdown Content:') + 1
    except ValueError:
        return []
    lines = lines[start:]
    pubs = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith('['):
            i += 1
            continue
        title_match = re.search(r'\[(.+?)\]', line)
        link_match = re.search(r'\((https://scholar.google.com/citations[^)]+)\)', line)
        if not title_match or not link_match:
            i += 1
            continue
        title = title_match.group(1)
        link = link_match.group(1)
        id_match = re.search(r'citation_for_view=[^:]+:([^&]+)', link)
        gs_id = id_match.group(1) if id_match else ''
        authors = lines[i + 1] if i + 1 < len(lines) else ''
        j = i + 2
        while j < len(lines) and not lines[j]:
            j += 1
        info = lines[j] if j < len(lines) else ''
        year_match = re.search(r'(19|20)\d{2}', info)
        year = year_match.group(0) if year_match else ''
        key = re.sub(r'[^A-Za-z0-9]+', '', title.split()[0]).lower() + year
        if year:
            pubs.append({
                'key': key,
                'title': title,
                'authors': authors,
                'year': year,
                'link': link,
                'gs_id': gs_id
            })
        i = j + 1
    return pubs


def write_bib(entries):
    with open(BIB_FILE, 'w') as f:
        f.write('---\n---\n\n')
        for e in entries:
            f.write(f"@misc{{{e['key']},\n")
            f.write(f"  title={{ {e['title']} }},\n")
            if e['authors']:
                f.write(f"  author={{ {e['authors']} }},\n")
            if e['year']:
                f.write(f"  year={{ {e['year']} }},\n")
            f.write(f"  html={{ {e['link']} }},\n")
            if e['gs_id']:
                f.write(f"  google_scholar_id={{ {e['gs_id']} }},\n")
            f.write('}\n\n')


def main():
    scholar_id = read_scholar_id()
    if not scholar_id:
        print('No scholar_userid found in', DATA_FILE)
        return
    text = fetch_page(scholar_id)
    pubs = parse_publications(text)
    write_bib(pubs)
    print(f'Updated {len(pubs)} publications')


if __name__ == '__main__':
    main()
