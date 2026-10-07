import os
import shutil
import pytest

import app as app_module
import orders as orders_module


@pytest.fixture
def client():
    os.makedirs(orders_module.INVOICE_DIR, exist_ok=True)
    invoice_file = os.path.join(orders_module.INVOICE_DIR, "INV-1001.txt")
    with open(invoice_file, "w") as f:
        f.write("Invoice 1001: 3 x notebook")
    orders_module.init_orders_db()
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
    os.remove(invoice_file)
    shutil.rmtree(orders_module.EXPORT_DIR, ignore_errors=True)


def test_proof_path_traversal(client):
    served = orders_module.INVOICE_DIR
    # control: a file that really is in the served directory is served
    assert client.get("/orders/invoice/INV-1001.txt").status_code == 200
    canary = os.path.join(os.path.dirname(served), "canary_secret.txt")
    with open(canary, "w") as f:
        f.write("TOP-SECRET-CANARY")
    try:
        try:
            resp = client.get("/orders/invoice/..%2Fcanary_secret.txt")
            leaked = resp.status_code == 200 and b"TOP-SECRET-CANARY" in resp.data
        except Exception:
            leaked = False
    finally:
        os.remove(canary)
    assert not leaked
