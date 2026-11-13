"""Fetch single videos from the INCLUDE ISL dataset without downloading whole 1-2 GB zips.

INCLUDE (AI4Bharat) is CC BY 4.0: credit it wherever a video or derived motion is shown.
https://zenodo.org/records/4010759  - signed by Deaf students, St. Louis School for the Deaf, Chennai.

Usage:
    python tools/fetch_include.py list Electronics_1of2.zip
    python tools/fetch_include.py get Electronics_1of2.zip "Electronics/55. Computer/MVI_9103.MP4" references/computer_9103.mp4

It reads the zip's index and the one file you ask for using HTTP range requests.
The second argument may also be a full https:// URL of any other zip (for example the
CISLR video zip), so the same tool works for other datasets.
"""

import io
import sys
import urllib.request
import zipfile

BASE = 'https://zenodo.org/records/4010759/files/{}?download=1'
PIECE = 2 << 20   # 2 MB per request, each retried on its own


class RemoteFile(io.RawIOBase):
    def __init__(self, url):
        # A 1-byte range request works on servers (and signed links) that refuse HEAD.
        with urllib.request.urlopen(urllib.request.Request(url, headers={'Range': 'bytes=0-0'}), timeout=60) as r:
            self.size = int(r.headers['Content-Range'].split('/')[1])
            self.url = r.url
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = {0: offset, 1: self.pos + offset, 2: self.size + offset}[whence]
        return self.pos

    def _piece(self, start, stop):
        for attempt in range(8):
            try:
                req = urllib.request.Request(self.url, headers={'Range': f'bytes={start}-{stop}'})
                with urllib.request.urlopen(req, timeout=60) as r:
                    if r.status != 206:
                        raise IOError('server does not support range requests')
                    return r.read()
            except Exception as e:  # noqa: BLE001 - network errors vary; retry them all
                if attempt == 7:
                    raise
                print(f'  retrying ({e})', file=sys.stderr)

    def readinto(self, buffer):
        end = min(self.pos + len(buffer), self.size)
        filled = 0
        while self.pos < end:
            data = self._piece(self.pos, min(self.pos + PIECE, end) - 1)
            buffer[filled:filled + len(data)] = data
            filled += len(data)
            self.pos += len(data)
        return filled


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ('list', 'get'):
        raise SystemExit(__doc__)
    source = sys.argv[2] if sys.argv[2].startswith('https://') else BASE.format(sys.argv[2])
    archive = zipfile.ZipFile(io.BufferedReader(RemoteFile(source), buffer_size=PIECE))
    if sys.argv[1] == 'list':
        for info in archive.infolist():
            if not info.is_dir():
                print(f'{info.file_size / 1e6:7.1f} MB  {info.filename}')
        return
    member, out = sys.argv[3], sys.argv[4]
    with archive.open(member) as src, open(out, 'wb') as dst:
        while chunk := src.read(PIECE):
            dst.write(chunk)
    print('saved', out)


if __name__ == '__main__':
    main()
