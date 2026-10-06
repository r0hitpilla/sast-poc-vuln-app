import os
import sqlite3
import threading

from flask import Flask, request, send_file, abort

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")

# per-process cache of the last-checked role, keyed by a value that is NOT
# unique per request under concurrency (see /admin/data below).
_role_cache = {}
_role_cache_lock = threading.Lock()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY, username TEXT, role TEXT)"
    )
    conn.execute("DELETE FROM users")
    conn.executemany(
        "INSERT INTO users (username, role) VALUES (?, ?)",
        [("alice", "admin"), ("bob", "user"), ("carol", "user")],
    )
    conn.commit()
    conn.close()


@app.route("/search")
def search_users():
    """SQL injection: username is string-interpolated directly into the query."""
    username = request.args.get("username", "")
    conn = get_db()
    rows = conn.execute(
        "SELECT id, username, role FROM users WHERE username = ?", (username,)
    ).fetchall()
    conn.close()
    return {"results": [dict(r) for r in rows]}


from werkzeug.utils import safe_join

@app.route("/files/<path:filename>")
def get_file(filename):
    """Path traversal fixed with secure file serving"""
    from flask import abort
    
    full_path = safe_join(UPLOADS_DIR, filename)
    if not full_path or os.path.commonprefix([full_path, UPLOADS_DIR]) != UPLOADS_DIR.rstrip('/'):
        return abort(403)
    
    return send_file(full_path)


@app.route("/admin/data")
def admin_data():
    """Custom logic bug: role is resolved by a background thread and cached
    per-process keyed by request.remote_addr, not per-request. Under
    concurrent requests from behind the same proxy/NAT, one caller's
    elevated role can be read back by a different, less-privileged caller
    before the cache entry is refreshed for their own username."""
    username = request.args.get("username", "")
    client_key = request.remote_addr  # not unique per user behind shared NAT/proxy

    with _role_cache_lock:
        cached = _role_cache.get(client_key)

    if cached is None:
        conn = get_db()
        row = conn.execute(
            "SELECT role FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        role = row["role"] if row else "user"
        with _role_cache_lock:
            _role_cache[client_key] = role
    else:
        role = cached  # stale/foreign role served from cache, not re-checked

    if role != "admin":
        abort(403)

    return {"secret": "admin-only payload", "served_role": role}


if __name__ == "__main__":
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
