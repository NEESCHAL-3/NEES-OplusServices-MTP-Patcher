#!/usr/bin/env python3
"""Publish a per-request release after the read-only patch job succeeds."""
import json
import os
from pathlib import Path
import re
import subprocess
from web_status import post_status


def main():
    data = json.loads(Path('package/metadata.json').read_text())
    device, issue, mode = data['codename'], data['issue'], data['mode']
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{1,39}', device) or issue != event['issue']['number'] or mode != 'automatic':
        raise ValueError('Invalid package metadata.')
    name = f'{device}-mtp-patched-{issue}.zip'
    if data['name'] != name:
        raise ValueError('Package filename mismatch.')
    tag = f'mtp-{issue}-{device}'
    repo = os.environ['GITHUB_REPOSITORY']
    notes = f"Generated MTP / USB UI patch package for **{device}** (user-supplied codename).\n\nRequest: #{issue}\nCompatibility mode: **{mode}**\n\nStructural verification passed. The generated output has not been device-tested. A codename is a package label, not a compatibility guarantee. Keep your original JAR and test reversibly.\n\nThe ZIP includes the patched JAR, SHA-256 checksum, patch report, and usage notes. The separate .sha256 file checks the ZIP itself.\n"
    Path('release-notes.txt').write_text(notes)
    # A rerun reuses the same release and replaces its matching assets.
    exists = subprocess.run(['gh', 'release', 'view', tag, '--repo', repo], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not exists:
        command = ['gh', 'release', 'create', tag, '--repo', repo, '--target', os.environ['GITHUB_SHA'], '--title', f'{device} · MTP patch · #{issue}', '--notes-file', 'release-notes.txt', '--latest=false', '--draft']
        subprocess.run(command, check=True)
    subprocess.run(['gh', 'release', 'upload', tag, str(Path('package') / name), str(Path('package') / f'{name}.sha256'), '--repo', repo, '--clobber'], check=True)
    # Keep a new release private until both downloads have been uploaded.
    subprocess.run(['gh', 'release', 'edit', tag, '--repo', repo, '--draft=false', '--latest=false'], check=True)
    post_status('ready', f'{name} is ready. Structural verification passed; this generated output has not been device-tested. Read the included report before installation.', f'https://github.com/{repo}/releases/download/{tag}/{name}')


if __name__ == '__main__':
    main()
