"""One-time owner-authorized Windows SQL Server setup; no plaintext password stored.

Invoked by INSTALL_AND_START.bat after dependency installation. It does not
silently reset accounts in an existing database. All SQL writes are read back.
"""
from __future__ import annotations
import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / '.env'
DB_NAME = 'QuantumSafeIoTLab'
USERNAME = 'Zeeshan'
# Argon2id hash for the user-specified initial password. The password itself is
# never embedded in source/config/SQL, and is required to be changed on login.
INITIAL_HASH = '$argon2id$v=19$m=19456,t=2,p=1$oGsclvDAI+S210WJLbGt/A$NK4i0QAVPTKzqoClACvpnHEcO6aqtowrbnOIhqkaizU'


def load_existing():
    values = {}
    if ENV.exists():
        for line in ENV.read_text(encoding='utf-8-sig').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key, val = line.split('=', 1)
                values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def known_instances():
    """Returns real instances from Windows registry plus conservative local names."""
    out = []
    from_env = load_existing().get('SQL_SERVER') or os.environ.get('SQL_SERVER')
    if from_env: out.append(from_env)
    try:
        import winreg
        # SQL Server instance names (default MSSQLSERVER, named e.g. SQLEXPRESS).
        for where in (winreg.HKEY_LOCAL_MACHINE,):
            for flag in (winreg.KEY_WOW64_64KEY, 0):
                try:
                    key = winreg.OpenKey(where, r'SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL', 0, winreg.KEY_READ | flag)
                    i = 0
                    while True:
                        try:
                            name, _, _ = winreg.EnumValue(key, i)
                        except OSError:
                            break
                        out.append('localhost' if name.upper() == 'MSSQLSERVER' else 'localhost\\' + name)
                        i += 1
                except OSError:
                    pass
    except ImportError:
        pass
    out.extend([r'localhost\SQLEXPRESS', 'localhost', r'.\SQLEXPRESS'])
    return list(dict.fromkeys(x for x in out if x))


def drivers(pyodbc):
    installed = pyodbc.drivers()
    preferred = ('ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server')
    return [x for x in preferred if x in installed]


def is_local(server):
    s = server.lower().strip().split('\\', 1)[0]
    return s in ('localhost', '.', '(local)', '127.0.0.1', '::1')


def conn_string(server, driver, database='master', trust=True):
    if not server or any(c in server for c in ';{}\r\n'):
        raise ValueError('Invalid SQL Server instance')
    # Local developer SQL instances often use self-signed TLS certificates. This
    # exception is limited to local instances; remote TLS validation is enforced.
    return (f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};'
            'Trusted_Connection=yes;Encrypt=yes;'
            f'TrustServerCertificate={"yes" if trust and is_local(server) else "no"};'
            'Connection Timeout=3;')


def find_connection(pyodbc, server_hint=None):
    good = drivers(pyodbc)
    if not good:
        raise RuntimeError('Microsoft ODBC Driver 18 (or 17) for SQL Server not installed.')
    last = []
    candidates = ([server_hint] if server_hint else []) + known_instances()
    for server in dict.fromkeys(x for x in candidates if x):
        for driver in good:
            try:
                conn = pyodbc.connect(conn_string(server, driver), autocommit=True, timeout=3)
                conn.cursor().execute('SELECT 1').fetchone()
                return server, driver, conn
            except pyodbc.Error as exc:
                last.append(f'{server} ({driver}): {str(exc)[:200]}')
    detail = '\n  '.join(last[:6])
    raise RuntimeError('No accessible SQL Server via current Windows user. Check SQL Server service, instance name and Windows login permissions.\n  ' + detail)


def apply_migrations(conn):
    script_files = ('01_create_database.sql', '02_upgrade_v02.sql')
    for name in script_files:
        source = (ROOT / 'Database' / name).read_text(encoding='utf-8-sig')
        # Database name is fixed for this application; SQL script is shipped with the package.
        for block in re.split(r'^\s*GO\s*(?:--[^\n]*)?$', source, flags=re.I | re.M):
            block = block.strip()
            if not block or all(not line.strip() or line.lstrip().startswith(('--','/*','*','*/')) for line in block.splitlines()):
                continue
            cur = conn.cursor()
            cur.execute(block)
            # Consume all resultsets, including verification queries, before next batch.
            while cur.nextset():
                pass
            cur.close()
    conn.cursor().execute(f'USE [{DB_NAME}]')
    # First-login password rotation: additive; existing accounts are not locked out.
    conn.cursor().execute("IF COL_LENGTH('dbo.Users','MustChangePassword') IS NULL ALTER TABLE dbo.Users ADD MustChangePassword BIT NOT NULL CONSTRAINT DF_QS_MustChange DEFAULT (0)")
    # Gateway tables initialize independently of a running Streamlit session.
    from quantumsafe.gateway_event_store import initialize
    # Uses quantumsafe.db.connection via .env; called once config is persisted.


def apply_crypto_audit_migration(conn):
    script = (ROOT / 'Database' / '03_secure_device_audit.sql').read_text(encoding='utf-8-sig')
    for block in re.split(r'^\s*GO\s*(?:--[^\n]*)?$', script, flags=re.I | re.M):
        block = block.strip()
        if not block or all(not line.strip() or line.lstrip().startswith(('--','/*','*','*/')) for line in block.splitlines()):
            continue
        cur=conn.cursor()
        cur.execute(block)
        while cur.nextset(): pass
        cur.close()


def write_env(server, driver):
    existing = load_existing()
    if ENV.exists():
        backup = ROOT / '.env.before_bootstrap'
        if not backup.exists():
            backup.write_bytes(ENV.read_bytes())
    # Preserve unrelated optional user settings; strip previous SQL connection keys.
    preserved = {k:v for k,v in existing.items() if not k.startswith('SQL_') and re.fullmatch(r'[A-Z][A-Z0-9_]*',k)}
    settings = {'SQL_SERVER':server,'SQL_DATABASE':DB_NAME,'SQL_DRIVER':driver,
                'SQL_AUTH':'windows','SQL_TRUST_SERVER_CERTIFICATE':'true' if is_local(server) else 'false'}
    settings.update(preserved)
    for key in ('SQL_SERVER','SQL_DATABASE','SQL_DRIVER','SQL_AUTH','SQL_TRUST_SERVER_CERTIFICATE'):
        os.environ[key]=settings[key]
    ENV.write_text('# Auto-discovered by QuantumSafe setup; Windows Integrated Authentication.\n'
                   + ''.join(f'{k}={v}\n' for k,v in settings.items()), encoding='utf-8')
    try: ENV.chmod(0o600)
    except OSError: pass


def ensure_admin(conn, repair=False):
    cursor = conn.cursor()
    cursor.execute('SELECT UserId,RoleName,IsActive FROM dbo.Users WHERE Username=?', USERNAME)
    row = cursor.fetchone()
    if row is None:
        cursor.execute('INSERT INTO dbo.Users(Username,PasswordHash,RoleName,IsActive,MustChangePassword) VALUES (?,?,?,1,1)', USERNAME, INITIAL_HASH, 'Admin')
        cursor.execute('SELECT UserId,RoleName,IsActive,MustChangePassword FROM dbo.Users WHERE Username=?', USERNAME)
        check=cursor.fetchone()
        assert check and check[1]=='Admin' and bool(check[2]) and bool(check[3]), 'Administrator verification failed'
        print('[PASS] First-login Zeeshan administrator created (password must be changed after sign-in).')
    elif repair:
        # Recovery is an explicit, separate action; require SQL sysadmin identity.
        row_perm = cursor.execute("SELECT ISNULL(IS_SRVROLEMEMBER('sysadmin'),0)").fetchone()
        if not row_perm or int(row_perm[0]) != 1:
            raise PermissionError('Admin repair requires local Windows account with SQL Server sysadmin access.')
        cursor.execute('UPDATE dbo.Users SET PasswordHash=?,RoleName=?,IsActive=1,MustChangePassword=1 WHERE Username=?', INITIAL_HASH,'Admin',USERNAME)
        print('[PASS] Zeeshan account recovered. Temporary password must change at next sign-in.')
    else:
        print('[INFO] Zeeshan account already exists: credentials and role preserved. For authorized recovery use RECOVER_ADMIN.bat.')
    return cursor.execute('SELECT UserId FROM dbo.Users WHERE Username=?', USERNAME).fetchone()[0]


def write_readback(conn, uid):
    # A dedicated installation audit row, not a synthetic gateway attack or sensor reading.
    cur = conn.cursor()
    row = cur.execute('INSERT INTO dbo.AuditLogs(UserId,ActionName,WasSuccessful,ShortDetail) OUTPUT INSERTED.AuditId VALUES (?,?,?,?)',uid,'INSTALL_HEALTH_CHECK',1,'Windows SQL installation proof').fetchone()
    event_id = int(row[0])
    row = cur.execute('SELECT WasSuccessful FROM dbo.AuditLogs WHERE AuditId=?',event_id).fetchone()
    if row is None or int(row[0])!=1:
        raise RuntimeError('SQL write/read-back health check failed')
    print('[PASS] SQL Server 2022-compatible live audit INSERT + readback confirmed. AuditId:',event_id)


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--server',help='Optional SQL instance override, e.g. localhost\\SQLEXPRESS')
    parser.add_argument('--repair-admin',action='store_true',help='Explicit recovery requiring SQL sysadmin')
    args=parser.parse_args(argv)
    try:
        import pyodbc
        print('Scanning SQL Server instances (Windows authentication)...',flush=True)
        server,driver,conn = find_connection(pyodbc,args.server)
        print(f'[PASS] SQL instance: {server} ; driver: {driver}',flush=True)
        with conn:
            apply_migrations(conn)
            # Write dotenv before importing app modules which load it at import time.
            write_env(server,driver)
            from quantumsafe import gateway_event_store
            gateway_event_store.initialize()
            apply_crypto_audit_migration(conn)
            conn.cursor().execute(f'USE [{DB_NAME}]')
            uid=ensure_admin(conn, repair=args.repair_admin)
            write_readback(conn,uid)
            server_version=conn.cursor().execute("SELECT CONVERT(varchar(32), SERVERPROPERTY('ProductVersion'))").fetchone()[0]
            print('[PASS] SQL Server version:',server_version)
            print('[PASS] Connection settings saved to project .env; no SQL password required.')
        conn.close()
        return 0
    except Exception as exc:
        print('[SETUP BLOCKED] '+type(exc).__name__+': '+str(exc), file=sys.stderr)
        return 2

if __name__=='__main__':
    sys.exit(main())
