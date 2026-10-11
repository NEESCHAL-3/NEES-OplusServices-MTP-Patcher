#!/usr/bin/env python3
"""Bounded HTTPS downloads. Resolve and pin public IPs for every redirect."""
import http.client
import ipaddress
import json
from pathlib import Path
import socket
import ssl
import sys
import time
import urllib.parse
from zipfile import ZipFile, BadZipFile

MAX_BYTES = 100 * 1024 * 1024
MAX_EXPANDED = 512 * 1024 * 1024


def normalize_url(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.hostname == 'drive.google.com':
        parts = parsed.path.split('/')
        file_id = parts[3] if len(parts) > 3 and parts[1:3] == ['file', 'd'] else urllib.parse.parse_qs(parsed.query).get('id', [''])[0]
        if not file_id or not all(c.isalnum() or c in '_-' for c in file_id):
            raise ValueError('Use a public Google Drive file link, not a folder link.')
        return 'https://drive.google.com/uc?' + urllib.parse.urlencode({'export': 'download', 'id': file_id})
    if parsed.hostname in ('www.dropbox.com', 'dropbox.com'):
        query = urllib.parse.parse_qs(parsed.query)
        query['dl'] = ['1']
        return urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query, doseq=True)))
    return url


def public_addresses(host):
    addresses = list(dict.fromkeys(item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)))
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError('Download links must resolve only to public internet addresses.')
    return addresses


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host, timeout=25, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        connection = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(connection, server_hostname=self.host)
        except Exception:
            connection.close()
            raise


def download(url, destination):
    url = normalize_url(url)
    deadline = time.monotonic() + 180
    for _ in range(6):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443) or parsed.fragment:
            raise ValueError('Every download redirect must be public HTTPS without credentials or custom ports.')
        addresses = public_addresses(parsed.hostname)
        connection = PinnedHTTPS(parsed.hostname, addresses[0])
        try:
            path = urllib.parse.urlunsplit(('', '', parsed.path or '/', parsed.query, ''))
            connection.request('GET', path, headers={'User-Agent': 'NEES-MTP-Workshop/1.0', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader('Location')
                if not location:
                    raise ValueError('The download host returned an empty redirect.')
                url = urllib.parse.urljoin(url, location)
                continue
            if response.status != 200:
                raise ValueError('The file could not be downloaded. Make it publicly accessible and use a direct file link.')
            if int(response.getheader('Content-Length') or 0) > MAX_BYTES:
                raise ValueError('JAR exceeds the 100 MB upload limit.')
            count = 0
            with open(destination, 'wb') as output:
                while True:
                    if time.monotonic() > deadline:
                        raise ValueError('Download exceeded the three-minute time limit.')
                    block = response.read(64 * 1024)
                    if not block:
                        break
                    count += len(block)
                    if count > MAX_BYTES:
                        raise ValueError('JAR exceeds the 100 MB upload limit.')
                    output.write(block)
            validate_archive(destination)
            return
        finally:
            connection.close()
    raise ValueError('Too many download redirects. Use a direct HTTPS file link.')


def validate_archive(path):
    try:
        with ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > 10000 or sum(entry.file_size for entry in entries) > MAX_EXPANDED:
                raise ValueError('JAR exceeds the expanded size or entry-count limit.')
            names = [entry.filename for entry in entries]
            if len(set(names)) != len(names):
                raise ValueError('JAR contains duplicate entries.')
            if not {'classes.dex', 'classes2.dex'}.issubset(names):
                raise ValueError('This is not the expected OplusServices JAR: required DEX entries are missing.')
            for entry in entries:
                parts = entry.filename.replace('\\', '/').split('/')
                if entry.filename.startswith(('/', '\\')) or '..' in parts or entry.flag_bits & 1:
                    raise ValueError('JAR contains unsafe or encrypted entries.')
                if entry.compress_type not in (0, 8):
                    raise ValueError('JAR uses an unsupported compression method.')
            for name in ('classes.dex', 'classes2.dex'):
                with archive.open(name) as dex:
                    if not dex.read(8).startswith(b'dex\n'):
                        raise ValueError('JAR contains an invalid DEX header.')
    except BadZipFile:
        raise ValueError('The link returned a webpage or invalid JAR. For Google Drive, enable Anyone with the link; large files may need a direct download host.') from None


def main():
    try:
        data = json.loads(Path('.work/request.json').read_text())
        Path('input').mkdir(exist_ok=True)
        download(data['url'], Path('input/oplus-services.jar'))
        # patch.sh resets .work; preserve validated metadata outside that directory.
        Path('output/request.json').write_text(json.dumps(data))
        print('Downloaded and validated JAR. The input file will never be executed.')
    except Exception as error:
        message = str(error) if isinstance(error, ValueError) else 'Download could not complete. Check that the file is public and try a direct HTTPS link.'
        Path('.work/web-error.txt').write_text(message)
        print(message, file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
