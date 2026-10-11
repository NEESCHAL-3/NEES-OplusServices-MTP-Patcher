import io
from contextlib import chdir
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from web_request import parse_request
from web_download import normalize_url, public_addresses, validate_archive, download
import web_package


def body(device='rodin', url='https://example.com/original.jar', mode='tested', checked=True):
    mark = 'x' if checked else ' '
    return f'### Device codename\n\n{device}\n\n### JAR download URL\n\n{url}\n\n### Compatibility mode\n\n{mode}\n\n### Public sharing\n\n- [{mark}] I can share this file publicly and understand that requests and release packages are public.\n'


class RequestTests(unittest.TestCase):
    def test_codename_and_modes(self):
        self.assertEqual(parse_request(body('Rosemary', mode='experimental'))['codename'], 'rosemary')
        self.assertEqual(parse_request(body())['mode'], 'automatic')

    def test_no_compatibility_choice_required(self):
        request = body().replace('### Compatibility mode\n\ntested\n\n', '')
        self.assertEqual(parse_request(request)['mode'], 'automatic')

    def test_browser_tracking_marker_preserves_request(self):
        request = '<!-- mtp-ticket:aca8032e-78cb-4b91-a8f1-790e36f09b53 -->\n\n' + body('rosemary')
        self.assertEqual(parse_request(request)['codename'], 'rosemary')

    def test_shell_and_markdown_injection_rejected(self):
        for device in ('../rodin', 'rodin; touch bad', 'rodin\nOTHER=value', '-rodin', 'a'*41):
            with self.subTest(device=device), self.assertRaises(ValueError):
                parse_request(body(device))
        with self.assertRaises(ValueError):
            parse_request(body() + '\n### Device codename\n\nother')

    def test_private_link_forms_and_consent(self):
        for url in ('http://example.com/a.jar', 'https://user:pass@example.com/a', 'https://example.com:8080/a', 'https://example.com/a#secret', 'https://example.com/a\ncommand'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_request(body(url=url))
        with self.assertRaises(ValueError):
            parse_request(body(checked=False))


class DownloadTests(unittest.TestCase):
    def test_hosts(self):
        self.assertEqual(normalize_url('https://drive.google.com/file/d/abc_123/view?usp=sharing'), 'https://drive.google.com/uc?export=download&id=abc_123')
        self.assertIn('dl=1', normalize_url('https://www.dropbox.com/s/a/file.jar?dl=0'))
        with self.assertRaises(ValueError):
            normalize_url('https://drive.google.com/drive/folders/abc')

    def test_public_dns_pinning(self):
        def record(ip):
            return (socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, 443))
        for addresses in ([record('127.0.0.1')], [record('10.0.0.1')], [record('169.254.169.254')], [record('8.8.8.8'), record('192.168.1.1')]):
            with patch('web_download.socket.getaddrinfo', return_value=addresses), self.assertRaises(ValueError):
                public_addresses('host.test')
        with patch('web_download.socket.getaddrinfo', return_value=[record('8.8.8.8')]):
            self.assertEqual(public_addresses('host.test'), ['8.8.8.8'])

    def test_redirects_revalidate_destination(self):
        class Response:
            status = 302
            def getheader(self, name):
                return 'http://127.0.0.1/private'
        class Connection:
            def __init__(self, *args): pass
            def request(self, *args, **kwargs): pass
            def getresponse(self): return Response()
            def close(self): pass
        with patch('web_download.public_addresses', return_value=['8.8.8.8']), patch('web_download.PinnedHTTPS', Connection), self.assertRaises(ValueError):
            download('https://host.test/file.jar', 'unused')

    def test_archive_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            jar = Path(directory) / 'input.jar'
            with ZipFile(jar, 'w') as archive:
                archive.writestr('classes.dex', b'dex\n035\0data')
                archive.writestr('classes2.dex', b'dex\n035\0data')
            validate_archive(jar)
            with patch('web_download.MAX_EXPANDED', 1), self.assertRaises(ValueError):
                validate_archive(jar)
            with ZipFile(jar, 'a') as archive:
                archive.writestr('../escape', b'bad')
            with self.assertRaises(ValueError):
                validate_archive(jar)
            jar.write_text('<html>not a download</html>')
            with self.assertRaises(ValueError):
                validate_archive(jar)


class PackageTests(unittest.TestCase):
    def test_each_device_gets_its_own_package_and_metadata(self):
        previous = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as directory, chdir(directory):
                Path('output').mkdir()
                for device, issue in (('rodin', 142), ('rosemary', 143)):
                    Path('output/request.json').write_text(json.dumps({'codename':device, 'issue':issue, 'mode':'automatic', 'url':'https://example.com/private-query'}))
                    Path('output/PATCH-INFO.txt').write_text('Structural checks PASS\n')
                    Path('output/SHA256.txt').write_text('hash  oplus-services-patched.jar\n')
                    Path('output/oplus-services-patched.jar').write_bytes(b'fixture')
                    with patch.dict(os.environ, {'GITHUB_REPOSITORY':'owner/repo', 'GITHUB_RUN_ID':'99', 'GITHUB_SHA':'abc123'}):
                        web_package.main()
                    name = f'{device}-mtp-patched-{issue}.zip'
                    with ZipFile(Path('package') / name) as archive:
                        self.assertEqual(set(archive.namelist()), {'oplus-services-patched.jar','SHA256.txt','PATCH-INFO.txt','README.txt'})
                        self.assertIn(device, archive.read('PATCH-INFO.txt').decode())
                    self.assertNotIn('url', json.loads(Path('package/metadata.json').read_text()))
                    self.assertTrue((Path('package') / f'{name}.sha256').exists())
        finally:
            os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
