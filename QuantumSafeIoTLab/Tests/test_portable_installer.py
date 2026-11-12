"""Installer checks runnable without SQL Server/Windows; live SQL is Windows-only."""
import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('qs_installer',ROOT/'SourceCode'/'bootstrap_sql.py')
mod=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(mod)


def test_argon2_bootstrap_password_is_correct():
    from argon2 import PasswordHasher
    assert PasswordHasher().verify(mod.INITIAL_HASH,'123456789012')
    assert '$argon2id$' in mod.INITIAL_HASH


def test_local_tls_policy_and_remote_verification():
    s=mod.conn_string(r'localhost\SQLEXPRESS','ODBC Driver 18 for SQL Server')
    assert 'Trusted_Connection=yes' in s and 'Encrypt=yes' in s and 'TrustServerCertificate=yes' in s
    remote=mod.conn_string('sql.example.test','ODBC Driver 18 for SQL Server')
    assert 'TrustServerCertificate=no' in remote
    with pytest.raises(ValueError):mod.conn_string('bad;PWD=password','ODBC Driver 18 for SQL Server')


def test_env_autogeneration_preserves_non_sql_settings(tmp_path,monkeypatch):
    env=tmp_path/'.env'
    env.write_text('SQL_SERVER=old-server\nQUANTUMSAFE_SWIPL=C:\\Program Files\\swipl\\bin\\swipl.exe\n')
    monkeypatch.setattr(mod,'ROOT',tmp_path)
    monkeypatch.setattr(mod,'ENV',env)
    mod.write_env(r'localhost\SQLEXPRESS','ODBC Driver 18 for SQL Server')
    data=env.read_text()
    assert 'SQL_SERVER=localhost\\SQLEXPRESS' in data
    assert 'SQL_DATABASE=QuantumSafeIoTLab' in data
    assert 'QUANTUMSAFE_SWIPL=' in data
    assert 'SQL_SERVER=old-server' not in data
    assert (tmp_path/'.env.before_bootstrap').exists()


def test_odbc_driver_fallback_and_missing():
    class Fake:
        def __init__(self,d):self.d=d
        def drivers(self):return self.d
    assert mod.drivers(Fake(['ODBC Driver 17 for SQL Server']))==['ODBC Driver 17 for SQL Server']
    assert mod.drivers(Fake([]))==[]


def test_portable_launcher_wiring():
    start=(ROOT/'START_APP.bat').read_text()
    install=(ROOT/'INSTALL_AND_START.bat').read_text()
    assert '%~dp0' in start and '%~dp0' in install
    assert 'install_ready.marker' in start
    assert 'Install-QuantumSafe.ps1' in install
    assert not (ROOT/'.env').exists(), 'Do not include machine credentials/configuration in distributable'


def test_admin_first_login_gate():
    app=(ROOT/'SourceCode'/'app.py').read_text()
    assert 'password_change.required' in app
    assert app.index('password_change.required') < app.index('st.sidebar.title')
    ui=(ROOT/'SourceCode'/'quantumsafe'/'ui'/'password_change.py').read_text()
    assert 'MustChangePassword=0' in ui and 'passwords.verify' in ui


def test_sql_script_order_ensures_table_exists():
    source=(ROOT/'SourceCode'/'bootstrap_sql.py').read_text()
    assert "gateway_event_store.initialize()\n            apply_crypto_audit_migration(conn)" in source
    assert "CREATE TABLE" in (ROOT/'Database'/'01_create_database.sql').read_text()
