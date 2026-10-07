import pytest
import os
import shutil
import sys

# Make `import app` work when pytest runs from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as app_module
import orders as orders_module


@pytest.fixture
def client(tmp_path):
    # Set up the invoice directory and a test file
    os.makedirs(orders_module.INVOICE_DIR, exist_ok=True)
    path = os.path.join(orders_module.INVOICE_DIR, "INV-1001.txt")
    with open(path, "w") as f:
        f.write("Invoice 1001: 3 x notebook")
    
    # Set up export directory
    os.makedirs(orders_module.EXPORT_DIR, exist_ok=True)
    
    orders_module.init_orders_db()
    app_module.app.config["TESTING"] = True
    
    with app_module.app.test_client() as c:
        yield c
    
    # Clean up
    os.remove(path)
    shutil.rmtree(orders_module.EXPORT_DIR, ignore_errors=True)


def test_proof_command_injection(client, tmp_path):
    canary = tmp_path / "pwned"
    
    # Control: an ordinary value works
    assert client.get("/orders/export", query_string={"name": "march"}).status_code == 200
    
    try:
        # The payload uses shell metacharacter to inject a command
        # The trailing " #" makes the shell ignore anything appended by the app
        client.get("/orders/export", query_string={"name": f"x; touch {canary} #"})
    except Exception:
        pass
    
    # If the vulnerability exists, the canary file would be created
    # So we assert it does NOT exist to prove the fix works
    assert not canary.exists()
