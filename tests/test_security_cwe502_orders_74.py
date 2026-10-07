import pytest
import os
import shutil
import tempfile

import app as app_module
import orders as orders_module


@pytest.fixture
def client():
    # Set up the invoice directory and a dummy invoice file
    os.makedirs(orders_module.INVOICE_DIR, exist_ok=True)
    path = os.path.join(orders_module.INVOICE_DIR, "INV-1001.txt")
    with open(path, "w") as f:
        f.write("Invoice 1001: 3 x notebook")

    # Initialize the database
    orders_module.init_orders_db()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c

    # Clean up
    os.remove(path)
    shutil.rmtree(orders_module.EXPORT_DIR, ignore_errors=True)


def test_proof_unsafe_yaml(client, tmp_path):
    canary = tmp_path / "pwned"
    
    # Control: a normal document is accepted
    resp = client.post("/orders/import", 
                       data="orders: []", 
                       content_type="text/yaml")
    assert resp.status_code == 200

    # Evil payload that should trigger os.system if unsafe
    evil = f'!!python/object/apply:os.system ["touch {canary}"]'
    
    try:
        client.post("/orders/import", data=evil, content_type="text/yaml")
    except Exception:
        pass
    
    # If the vulnerability exists, the canary would be created.
    # With a safe loader, it should not exist.
    assert not canary.exists()
