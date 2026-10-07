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

## Bugs in orders.py (second demo set)

`orders.py` is a second feature module (orders, invoices, payments), added so
a demo has fresh findings after the first set was fixed.

| Endpoint | Problem | CWE | Found by |
|---|---|---|---|
| `GET /orders/search?customer=` | SQL injection (f-string query). Carries a comment aimed at the AI reviewer, to show the prompt-injection defence | CWE-89 | Semgrep |
| `GET /orders/export?name=` | Command injection (`tar` run with `shell=True`) | CWE-78 | Semgrep |
| `POST /orders/import` | Unsafe `yaml.load` on request data | CWE-502 | Semgrep |
| `GET /orders/receipt?note=` | Template injection / XSS (`render_template_string` on an f-string) | CWE-79 | Semgrep |
| `GET /orders/invoice/<name>` | Path traversal (`send_file` on a joined path) | CWE-22 | Semgrep (custom rule) |
| `POST /orders/notify` | TLS certificate checking disabled (`verify=False`) | CWE-295 | Semgrep |
| `POST /orders/charge` | Hard-coded API key | CWE-798 | gitleaks |
| `requirements.txt` | `requests==2.31.0` has known vulnerabilities | CWE-1395 | osv-scanner |

## Run

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python app.py
