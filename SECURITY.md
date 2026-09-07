# Security

## Why this file is not boilerplate

This tower does the opposite of the validator beside it. `iirds-validate`
opens files that arrive from outside and never touches the network; this
fetches from machines nobody here controls and **publishes what comes back**,
into a page people read and a feed people point a reader at.

So the working assumption is not "hostile input arrives", it is "everything
this publishes was written by someone else".

## What is defended, and where the proof lives

| threat | defence | pinned by |
|---|---|---|
| The credential this cron holds travelling to a host it does not belong to. The decision used to be whether `api.github.com` occurred anywhere in the URL, and it occurs in `https://example.invalid/api.github.com` too — while adding a source here is a row in `sources.json` rather than a patch | the decision is a function of the parsed host and scheme: `https` and a hostname equal to the API's, or no credential | `tests/test_credential_scope.py`, one case per spelling, each wrong on the host only |
| The same credential carried by a redirect. `urllib` rebuilds the request for the new location with every header except `content-length` and `content-type`, whatever host it is now talking to — so a source that simply moves takes the token with it | a redirect that leaves the host it started on, or steps down from https to http, is refused rather than followed | `tests/test_redirects.py`, with the handler exercised directly |
| Text this tower did not write, in the files it publishes. A release title carrying `](` closes the link it sits in and opens another one, on a page whose content is links; a URL carrying `)` does it from the other end | link and emphasis markers are escaped into `WATCH.md`, the target is percent-encoded, and line breaks become spaces so a title cannot write a table row. `feed.xml` has escaped its titles since it was written | `tests/test_published_text.py`, including one test that writes the page and reads it back — the escapers having cases says nothing about whether the page calls them |
| A body larger than anything a source of this kind sends | reads stop at 8 MiB and refuse; truncating would hash a prefix, and a hash of a prefix moves whenever the prefix does | `tests/test_read_limit.py` |
| A source that quietly stops being what it was | a refused redirect and an oversized answer are **published as events**, in the same shape and the same memory as anything else that moved, rather than left as a row that stopped updating | `tests/test_redirects.py`, `tests/test_read_limit.py` |
| Dependency drift | there are no dependencies: standard library only, on purpose. A watcher that needs an update is a watcher that eventually stops watching | `pyproject.toml`, and the absence of a lock step in the cron |

## What is not defended, and is worth knowing

- **The sources are trusted to be who they say.** Transport is verified TLS,
  which is what says the host is that host; nothing here checks that the
  content is what the standards body meant to publish. A compromised upstream
  publishes through this tower like any other change.
- **The tower's memory is a file in this repository.** `state.json` is the
  record of what has been seen; anyone who can commit here can change what the
  tower believes it already reported. Its git history is the audit trail, and
  that is the whole of the mechanism.
- **A page that changes on every request looks like news.** One source hashes
  the schema file rather than the page that links it, because the page carries
  a per-request token; a source added without that care will report a move
  daily. That is a correctness problem, not a security one, but it is the way
  this tower is most likely to become unreadable.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting on this repository
("Security" → "Report a vulnerability") rather than a public issue. The most
serious bug this tower can have is publishing something a reader trusts and
should not — a link that goes somewhere the source chose, or a credential that
left this machine.

Supported versions: whatever `main` runs today. There is no release to pin.
