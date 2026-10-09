# sample-vuln-app

Deliberately vulnerable Flask app used as a demo target for the
sast-autofix-poc pipeline. Do not deploy this anywhere reachable.

## Bugs (for demo narration)

1. `GET /search?username=...` — SQL injection (CWE-89), string-interpolated
   query.
2. `GET /files/<path:filename>` — path traversal (CWE-22), no containment
   check before `send_file`.
3. `GET /admin/data?username=...` — role cached per-client-address instead
   of per-username, so a shared NAT/proxy client can read back another
   user's cached admin role (race/logic bug, not a canned CWE snippet).

## Bugs in tickets.py (third demo set)

`tickets.py` is a support-tickets feature (token auth via `X-Api-Token`;
demo tokens `tok-ann`, `tok-raj`), added so a demo has fresh findings.

| Endpoint | Problem | CWE | Found by |
|---|---|---|---|
| `GET /tickets/search?q=&sort=` | SQL injection: `q` goes into an f-string `LIKE`, and `sort` is concatenated into `ORDER BY`. `sort` is an identifier, so a bound parameter can't fix it; it needs an allowlist | CWE-89 | Semgrep |
| `GET /tickets/<id>` | BOLA / IDOR: any valid token can read any ticket, e.g. raj reads ann's refund ticket | CWE-639 | Not found by stock Semgrep rules |
| `POST /tickets/<id>/close` | BOLA / IDOR: any valid token can close any user's ticket | CWE-639 | Not found by stock Semgrep rules |

## Run

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python app.py
