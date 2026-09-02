import os
import tempfile

import pytest

# Must be set before app.config (and anything importing it) is ever imported --
# config.py reads these at import time to compute LIBRARY_PATH/CONFIG_PATH/DB_PATH.
_tmp = tempfile.mkdtemp(prefix="modelhub-test-")
os.environ["LIBRARY_PATH"] = os.path.join(_tmp, "data")
os.environ["CONFIG_PATH"] = os.path.join(_tmp, "config")
os.makedirs(os.environ["LIBRARY_PATH"], exist_ok=True)
os.makedirs(os.environ["CONFIG_PATH"], exist_ok=True)
# effectively disable the background scan loop firing mid-suite
os.environ["SCAN_INTERVAL_SECONDS"] = "999999"


@pytest.fixture(scope="session")
def library_path():
    return os.environ["LIBRARY_PATH"]


@pytest.fixture(scope="session")
def client():
    from starlette.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c
