#!/usr/bin/env python3
"""Package checked output. Codename is a label, never a compatibility claim."""
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    data = json.loads(Path('output/request.json').read_text())
    device, issue = data['codename'], data['issue']
    name = f'{device}-mtp-patched-{issue}.zip'
    report = Path('output/PATCH-INFO.txt')
    report.write_text(report.read_text() + f"\nDevice codename (user supplied): {device}\nCompatibility mode: {data['mode']}\nRequest: https://github.com/{os.environ['GITHUB_REPOSITORY']}/issues/{issue}\nWorkflow run: {os.environ['GITHUB_RUN_ID']}\nPatcher commit: {os.environ['GITHUB_SHA']}\n\nStructural checks passed. This generated output has not been device-tested.\nKeep the original JAR and test using a reversible installation method.\n")
    Path('package').mkdir(exist_ok=True)
    readme = f"NEES MTP patch for {device}\n\nThis archive contains the generated oplus-services-patched.jar.\nThe codename identifies this request, not verified device compatibility.\nRead PATCH-INFO.txt and verify SHA256.txt before use.\nNo installation or flashing is performed by this service.\nKeep your original oplus-services.jar. Test reversibly before permanent installation.\nA framework JAR mismatch can prevent booting.\n\nSource: https://github.com/{os.environ['GITHUB_REPOSITORY']}\n"
    with ZipFile(Path('package') / name, 'w', ZIP_DEFLATED) as archive:
        for filename in ('oplus-services-patched.jar', 'SHA256.txt', 'PATCH-INFO.txt'):
            archive.write(Path('output') / filename, filename)
        archive.writestr('README.txt', readme)
    sha = hashlib.sha256((Path('package') / name).read_bytes()).hexdigest()
    (Path('package') / f'{name}.sha256').write_text(f'{sha}  {name}\n')
    # Publish only constrained metadata; never carry the submitted URL to the write-token job.
    Path('package/metadata.json').write_text(json.dumps({'codename': device, 'issue': issue, 'mode': data['mode'], 'name': name}))


if __name__ == '__main__':
    main()
