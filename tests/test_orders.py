"""Functional tests for orders.py: legitimate use must keep working.

Like tests/test_app.py, these do NOT assert that the vulnerabilities are gone:
the autofix pipeline fixes one finding at a time and runs this suite after
each fix. The scanner checks for the bug; these check the fix kept the feature.
"""
import os
import shutil

import pytest
import requests

import app as app_module
import orders as orders_module

INVOICE = "INV-1001.txt"


@pytest.fixture
def client():
    os.makedirs(orders_module.INVOICE_DIR, exist_ok=True)
    path = os.path.join(orders_module.INVOICE_DIR, INVOICE)
    with open(path, "w") as f:
        f.write("Invoice 1001: 3 x notebook")
    orders_module.init_orders_db()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
    os.remove(path)
    shutil.rmtree(orders_module.EXPORT_DIR, ignore_errors=True)


def test_search_finds_a_customers_orders(client):
    resp = client.get("/orders/search?customer=ann")
    assert resp.status_code == 200
    items = [r["item"] for r in resp.get_json()["results"]]
    assert items == ["notebook", "pen"]


def test_search_unknown_customer_returns_nothing(client):
    assert client.get("/orders/search?customer=nobody").get_json()["results"] == []


def test_invoice_is_served(client):
    resp = client.get(f"/orders/invoice/{INVOICE}")
    assert resp.status_code == 200
    assert resp.data == b"Invoice 1001: 3 x notebook"
    resp.close()


@pytest.mark.skipif(shutil.which("tar") is None, reason="tar not installed")
def test_export_creates_an_archive(client):
    resp = client.get("/orders/export?name=march")
    assert resp.status_code == 200
    assert resp.get_json() == {"archive": "march.tgz"}
    assert os.path.exists(os.path.join(orders_module.EXPORT_DIR, "march.tgz"))


def test_import_reads_yaml_orders(client):
    body = "orders:\n  - {customer: ann, item: pen, qty: 2}\n  - {customer: raj, item: ink, qty: 1}\n"
    resp = client.post("/orders/import", data=body, content_type="text/yaml")
    assert resp.status_code == 200
    assert resp.get_json() == {"imported": 2, "customers": ["ann", "raj"]}


def test_receipt_shows_the_note(client):
    resp = client.get("/orders/receipt?note=Thanks+Ann")
    assert resp.status_code == 200
    assert b"Thanks Ann" in resp.data


def test_notify_posts_to_the_webhook(client, monkeypatch):
    class Reply:
        status_code = 202

    monkeypatch.setattr(requests, "post", lambda *a, **k: Reply())
    resp = client.post("/orders/notify", json={"id": 1})
    assert resp.status_code == 200
    assert resp.get_json() == {"status": 202}
