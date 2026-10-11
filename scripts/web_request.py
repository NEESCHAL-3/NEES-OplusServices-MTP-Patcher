#!/usr/bin/env python3
"""Validate public patch requests; no issue text is evaluated as shell code."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

FIELDS = ('Device codename', 'JAR download URL', 'Public sharing')


def parse_request(body):
    headings = list(re.finditer(r'^### ([^\r\n]+)\r?\n', body, re.M))
    values = {}
    for i, match in enumerate(headings):
        key = match.group(1).strip()
        if key in values:
            raise ValueError('Duplicate request field.')
        values[key] = body[match.end():headings[i + 1].start() if i + 1 < len(headings) else len(body)].strip()
    # Accept already-opened forms from the previous UI, but always inspect the
    # submitted JAR automatically regardless of the former mode choice.
    if not set(FIELDS).issubset(values) or set(values) - set(FIELDS) - {'Compatibility mode'}:
        raise ValueError('Use the website or the Patch request issue form to submit the required fields.')
    device = values['Device codename'].lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{1,39}', device):
        raise ValueError('Device codename must be 2–40 letters, numbers, hyphens, or underscores.')
    url = values['JAR download URL']
    if len(url) > 1800 or any(ord(char) < 33 or ord(char) > 126 for char in url):
        raise ValueError('Use a single, URL-encoded HTTPS download link of at most 1800 characters.')
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443) or parsed.fragment:
        raise ValueError('Only public HTTPS links without credentials, fragments, or custom ports are supported.')
    if not re.search(r'^- \[[xX]\] I can share this file publicly', values['Public sharing'], re.M):
        raise ValueError('Confirm public sharing before submitting a patch request.')
    return {'codename': device, 'url': url, 'mode': 'automatic'}


def check_limits(issue, repo, token):
    """Bound automated usage: three requests/person/day; twenty open requests."""
    request = urllib.request.Request(
        f'https://api.github.com/repos/{repo}/issues?state=all&sort=created&direction=desc&per_page=100',
        headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=20) as response:
        issues = json.load(response)
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)
    recent = [item for item in issues if not item.get('pull_request') and item['title'].startswith('[Patch request]') and dt.datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')) > cutoff]
    if sum(item['user']['login'] == issue['user']['login'] for item in recent) > 3:
        raise ValueError('Limit reached: three patch requests per GitHub account in 24 hours. Try again tomorrow.')
    # Check the full bounded open-issue page independently of recent history.
    request.full_url = f'https://api.github.com/repos/{repo}/issues?state=open&per_page=100'
    with urllib.request.urlopen(request, timeout=20) as response:
        open_issues = json.load(response)
    if sum(item['title'].startswith('[Patch request]') and not item.get('pull_request') for item in open_issues) > 20:
        raise ValueError('The workshop is busy. There are twenty open patch requests; please try again later.')


def main():
    error_file = Path('.work/web-error.txt')
    error_file.parent.mkdir(exist_ok=True)
    try:
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        issue = event['issue']
        if issue['user']['type'] != 'User':
            raise ValueError('Submit the request from a human GitHub account.')
        data = parse_request(issue.get('body') or '')
        if issue['title'] != f"[Patch request] {data['codename']}":
            raise ValueError('The request title must match the device codename. Submit a fresh request using the website.')
        check_limits(issue, os.environ['GITHUB_REPOSITORY'], os.environ['GH_TOKEN'])
        data['issue'] = issue['number']
        Path('.work/request.json').write_text(json.dumps(data))
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f"codename={data['codename']}\nmode={data['mode']}\nissue={issue['number']}\n")
        print('Request validated.')
    except Exception as error:
        message = str(error) if isinstance(error, ValueError) else 'Request validation could not complete. See the workflow run for details.'
        error_file.write_text(message)
        print(message, file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
