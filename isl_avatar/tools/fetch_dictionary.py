"""Find and download ISL dictionary videos from the team's shared Google Drive folders.

The folder list is registry/dictionary_folders.csv (Sr.No., Folder Name, Link), one Drive
folder per starting letter. Folders must be shared as "anyone with the link".

    python tools/fetch_dictionary.py find magnet           # list matching videos
    python tools/fetch_dictionary.py get magnet            # download every match into references/
    python tools/fetch_dictionary.py get "Magnet.mp4"      # download one exact file name

Saved as references/dict_<file name>. Record the source in registry/signs.csv.
"""

import csv
import html
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOLDERS = ROOT / 'registry' / 'dictionary_folders.csv'
LISTING = 'https://drive.google.com/embeddedfolderview?id={}'
DOWNLOAD = 'https://drive.usercontent.google.com/download?id={}&export=download&confirm=t'


def folder_ids():
    with open(FOLDERS, newline='', encoding='utf-8-sig') as f:
        rows = {r['Folder Name'].strip(): r['Link '.strip()] if 'Link' in r else r['Link '] for r in csv.DictReader(f)}
    return {name: re.search(r'folders/([A-Za-z0-9_-]+)', link).group(1) for name, link in rows.items()}


def list_folder(folder_id):
    with urllib.request.urlopen(LISTING.format(folder_id), timeout=60) as r:
        page = r.read().decode('utf-8', 'ignore')
    found = re.findall(r'href="https://drive\.google\.com/file/d/([A-Za-z0-9_-]+)/[^"]*"[^>]*>.*?'
                       r'<div class="flip-entry-title">([^<]+)</div>', page, re.S)
    return [(file_id, html.unescape(name)) for file_id, name in found]


def matches(term):
    term = term.strip()
    exact = term.lower().endswith('.mp4')
    first = term[0].upper()
    folders = folder_ids()
    folder = folders.get(first) or folders.get('Numbers')
    words = term.lower().replace(' ', '_')
    out = []
    for file_id, name in list_folder(folder):
        stem = name.lower()
        if exact and stem == term.lower():
            out.append((file_id, name))
        elif not exact and (stem == f'{words}.mp4' or stem.startswith(f'{words}_(')):
            out.append((file_id, name))   # "Magnet.mp4", "Magnet_(Sign_2).mp4", "Machine_(Explanation).mp4"
    return out


def download(file_id, name):
    out = ROOT / 'references' / f'dict_{name.replace(" ", "_")}'
    with urllib.request.urlopen(DOWNLOAD.format(file_id), timeout=300) as r, open(out, 'wb') as f:
        if 'text/html' in r.headers.get('Content-Type', ''):
            raise SystemExit(f'{name}: Drive returned a web page instead of the video (not shared publicly?)')
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return out


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ('find', 'get'):
        raise SystemExit(__doc__)
    found = matches(' '.join(sys.argv[2:]))
    if not found:
        raise SystemExit('No matching video found.')
    for file_id, name in found:
        if sys.argv[1] == 'find':
            print(f'{name}  (id {file_id})')
        else:
            print('saved', download(file_id, name))


if __name__ == '__main__':
    main()
