"""Foundation contract and read-only update validation tests."""
import io
import json
import zipfile
import pytest
from quantumsafe.module_contracts import COMPONENTS, get_contract
from quantumsafe.update_preflight import validate_update


def _package(tmp_path, entry="payload/SourceCode/quantumsafe/example.py"):
    path = tmp_path / "update.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("update.json", json.dumps({"product":"QuantumSafeIoTLab", "version":"0.6.1"}))
        archive.writestr(entry, "# test")
    return path


def test_contracts_have_unique_names():
    assert len({c.name for c in COMPONENTS}) == len(COMPONENTS)
    assert get_contract("edge_rf").status == "offline_only"
    assert get_contract("adaptive_learning").status == "planned"


def test_preflight_valid(tmp_path):
    manifest, paths = validate_update(_package(tmp_path))
    assert manifest["version"] == "0.6.1"
    assert paths == ("SourceCode/quantumsafe/example.py",)


@pytest.mark.parametrize("path", [
    "payload/../.env", "payload/SourceCode/.env", "payload/SourceCode/run.ps1",
    "payload/Database/change.sql", "payload/SourceCode/../.env",
    "payload/SourceCode\evil.py", "other/evil.py",
])
def test_preflight_rejects_unsafe(tmp_path, path):
    with pytest.raises(ValueError):
        validate_update(_package(tmp_path, path))
