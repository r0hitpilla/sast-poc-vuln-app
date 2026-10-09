"""Support tickets: a third feature module for the demo app.

Deliberately vulnerable (see README, "Bugs in tickets.py"). Do not deploy.
"""

import os
import sqlite3

from flask import Blueprint, abort, jsonify, request

tickets = Blueprint("tickets", __name__, url_prefix="/tickets")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TICKETS_DB = os.path.join(BASE_DIR, "tickets.db")

# Demo API tokens. A real service would look these up in its auth store.
API_TOKENS = {
    "tok-ann": "ann",
    "tok-raj": "raj",
}


def _db():
    conn = sqlite3.connect(TICKETS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_tickets_db():
    conn = _db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tickets ("
        "id INTEGER PRIMARY KEY, owner TEXT, subject TEXT, body TEXT, "
        "status TEXT, created TEXT)"
    )
    conn.execute("DELETE FROM tickets")
    conn.executemany(
        "INSERT INTO tickets (id, owner, subject, body, status, created) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "ann", "Login loop", "Cannot sign in on mobile", "open", "2026-10-01"),
            (2, "ann", "Refund request", "Card ending 4242, order 17", "open", "2026-10-03"),
            (3, "raj", "Address change", "New address: 12 Hill Rd", "open", "2026-10-02"),
        ],
    )
    conn.commit()
    conn.close()


def current_user():
    user = API_TOKENS.get(request.headers.get("X-Api-Token", ""))
    if user is None:
        abort(401)
    return user


@tickets.route("/search")
def search_tickets():
    user = current_user()
    term = request.args.get("q", "")
    term = request.args.get("q", "")
    sort = request.args.get("sort", "created")
    
    # Basic validation for sort column to prevent injection via ORDER BY clause
    allowed_sorts = ["id", "subject", "status", "created"]
    if sort not in allowed_sorts:
        abort(400)

    rows = _db().execute(
        "SELECT id, subject, status, created FROM tickets WHERE owner = ? AND subject LIKE ?",
        (user, f"%{term}%")
    ).fetchall()
    return jsonify({"results": [dict(r) for r in rows]})


@tickets.route("/<int:ticket_id>")
def get_ticket(ticket_id):
    current_user()
    current_user_data = current_user()
    user_obj = current_user()
    user = user_obj["id"] if isinstance(user_obj, dict) else user_obj

    row = _db().execute(
        "SELECT id, owner, subject, body, status, created FROM tickets WHERE id = ? AND owner = ?",
        (ticket_id, user),
    ).fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))


@tickets.route("/<int:ticket_id>/close", methods=["POST"])
def close_ticket(ticket_id):
    user_obj = current_user()
    user = user_obj["id"] if isinstance(user_obj, dict) else user_obj
    
    conn = _db()
    cur = conn.execute("UPDATE tickets SET status = 'closed' WHERE id = ? AND owner = ?", (ticket_id, user))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        abort(404)
    return jsonify({"id": ticket_id, "status": "closed"})
