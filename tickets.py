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
    sort = request.args.get("sort", "created")
    query = (
        f"SELECT id, subject, status, created FROM tickets "
        f"WHERE owner = '{user}' AND subject LIKE '%{term}%' "
        "ORDER BY " + sort
    )
    rows = _db().execute(query).fetchall()
    return jsonify({"results": [dict(r) for r in rows]})


@tickets.route("/<int:ticket_id>")
def get_ticket(ticket_id):
    current_user()
    row = _db().execute(
        "SELECT id, owner, subject, body, status, created FROM tickets WHERE id = ?",
        (ticket_id,),
    ).fetchone()
    if row is None:
        abort(404)
    return jsonify(dict(row))


@tickets.route("/<int:ticket_id>/close", methods=["POST"])
def close_ticket(ticket_id):
    current_user()
    conn = _db()
    cur = conn.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        abort(404)
    return jsonify({"id": ticket_id, "status": "closed"})
