# MTP Patcher

**[Open MTP Patcher](https://neeschal-3.github.io/NEES-MTP-Workshop/)**

The website is public and open to everyone. Sign in to GitHub to submit a patch request; viewing the site and downloading packages requires no login.

The patch service is a static GitHub Pages website, hosted separately from a private source repository, backed by this repository's issue events and Actions. There is no external backend and no credential in the browser.

## User flow

1. Enter a codename and public JAR link at the patch service.
2. Any OplusServices JAR can be submitted. The service automatically checks the code required by the patch; there is no fingerprint restriction or compatibility-mode choice.
3. Confirm public sharing and click **Start patch**.
4. GitHub opens a prefilled issue. Sign in and submit it without changing the field headings. The title must be `[Patch request] codename`.
5. Return to the patch service. A random marker in the prefilled issue lets this browser automatically locate its submission, including repeated requests for the same codename. Keep that marker in the submitted body. The page remembers pending and active requests locally; no issue number needs to be entered. Status comes from bot-owned comments, checked every 45 seconds while the page is visible. GitHub API rate limits may require using the issue/run links instead. Automatic recovery requires the same browser with its local storage intact; a saved `?job=` page link can reopen a found request elsewhere.
6. Successful verification publishes `<codename>-mtp-patched-<issue-number>.zip` and its `.sha256` file under release tag `mtp-<issue-number>-<codename>`. Requests are automatically closed after success or failure.

Packages contain `oplus-services-patched.jar`, `SHA256.txt`, `PATCH-INFO.txt`, and `README.txt`. The report records the original patcher's checks, input/output hashes, codename, automatic inspection policy, request, run, and source commit. Codename labels never imply device compatibility. No device installation is performed.

## Deployment

- Website source is kept in the private `NEESCHAL-3/NEES-MTP-Workshop` repository. Enable GitHub Pages there with **GitHub Actions** as its publishing source; this requires an eligible account plan.
- Keep Issues enabled. `.github/workflows/patch-request.yml` handles newly opened requests and must be on the default branch.
- Push `web/` changes to `main` in the private website repository; its Pages workflow deploys them. No website files are committed to the public patcher repo.
- The patch workflow declares its own permissions: preparation/reporting need `issues: write`, processing needs `contents: read`, publication needs `contents: write` and `issues: write`. No custom secret or personal access token is required.
- When moving to a different repository, change `REPO` in `web/app.js` and the explicit source/release/documentation links in `web/index.html` and README.

## Operational limits

- Public HTTPS only; no passwords, fragments, custom ports, private IP ranges, or redirects to them.
- Maximum download: 100 MB, three-minute transfer deadline, five redirects.
- Expanded JAR: 512 MB and 10,000 entries maximum; duplicate, encrypted, unsafe-path, or unsupported-compression entries are rejected.
- Three patch requests per account per day; twenty open patch requests maximum. History queries are bounded to the most recent 100 issues; high-volume repositories should add stronger quota accounting. These limits deter ordinary misuse and do not prevent coordinated abuse.
- Fifteen-minute processing-job timeout. GitHub runner availability controls start time; this service does not promise a strict FIFO queue.
- Inter-job artifacts expire after one day. Public release downloads persist until a maintainer removes them.

## Download hosts

Public Google Drive file links are normalized to the download endpoint; Dropbox share links use `dl=1`. Direct HTTPS URLs are supported if they serve the actual file. Google Drive confirmation/interstitial pages for some large files are rejected with a clear error; provide a direct download host instead. A sharing page, login page, or inaccessible file cannot be patched.

## Failure and recovery

Missing smali anchors, failed verification, and invalid downloads produce a failed request without an output release. Submit a fresh corrected request. Only repository maintainers can rerun workflows; a successful rerun reuses its release tag and replaces matching assets.

New releases remain drafts until both assets are uploaded. If publication fails, a draft may exist without both assets. The workflow reports failure; a maintainer can rerun the publisher or remove the incomplete release. Public links with credentials should never be submitted: if one is accidentally posted, revoke it at its source and remove it from the issue and Actions artifacts/logs as appropriate.

The source tree remains binary-free. Public releases intentionally distribute the generated output requested by the submitter. Package rights are not granted by the patcher's MIT source license.
