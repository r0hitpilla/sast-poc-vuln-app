import pytest
import requests
import os
import shutil

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


def test_proof_tls_verification_is_not_disabled(client, monkeypatch):
    calls = []

    class Reply:
        status_code = 200

    def fake(*args, **kwargs):
        calls.append(kwargs)
        return Reply()

    monkeypatch.setattr(requests, "post", fake)
    
    # Control: ensure the endpoint works normally
    resp = client.post("/orders/notify", json={"test": "data"})
    assert resp.status_code == 200

    # Test the vulnerability: verify that verify=False is not passed
    assert calls, "the endpoint made no outgoing call"
    assert all(kw.get("verify", True) is not False for kw in calls)
