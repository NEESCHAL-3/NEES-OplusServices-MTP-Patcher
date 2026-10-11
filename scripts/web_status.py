#!/usr/bin/env python3
"""Write bot-owned, machine-readable issue status. Never echo private URLs."""
import json
import os
from pathlib import Path
import sys
import urllib.request


def post_status(status, message, download_url=None):
    repo = os.environ['GITHUB_REPOSITORY']
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    issue = event['issue']['number']
    run = f"https://github.com/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    data = {'status': status, 'message': message, 'run_url': run}
    if download_url:
        data['download_url'] = download_url
    titles = {'patching': 'Patch in progress', 'ready': 'Package ready', 'failed': 'Patch stopped'}
    body = f"### {titles[status]}\n\n{message}\n\n[View workflow run]({run})"
    if download_url:
        body += f" · [Download package]({download_url})"
    body += '\n\n<!-- mtp-status ' + json.dumps(data) + ' -->'
    token = os.environ['GH_TOKEN']
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'}
    request = urllib.request.Request(f'https://api.github.com/repos/{repo}/issues/{issue}/comments', data=json.dumps({'body': body}).encode(), headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        response.read()
    if status in ('ready', 'failed'):
        payload = json.dumps({'state': 'closed', 'state_reason': 'completed' if status == 'ready' else 'not_planned'}).encode()
        request = urllib.request.Request(f'https://api.github.com/repos/{repo}/issues/{issue}', data=payload, headers=headers, method='PATCH')
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()


if __name__ == '__main__':
    status = sys.argv[1]
    if status == 'patching':
        message = 'Request accepted. GitHub is downloading your JAR, applying the patch, and checking the output. A release is published only after all structural checks pass.'
    else:
        error = Path('.work/web-error.txt')
        message = error.read_text()[:500] if error.exists() else 'The workflow did not complete. The input may be unsupported, patch anchors may not match, or the build checks may have failed. No release package was published. See the run for details.'
    post_status(status, message)
