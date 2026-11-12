"""Fast, honest start check. Prevents a broken login page when SQL is absent."""
import sys

def main():
    try:
        from quantumsafe import db
        with db.connection() as con:
            cur=con.cursor()
            server, database=cur.execute('SELECT @@SERVERNAME, DB_NAME()').fetchone()
            row=cur.execute("SELECT CASE WHEN OBJECT_ID(N'dbo.Users',N'U') IS NOT NULL AND OBJECT_ID(N'dbo.VirtualGatewayEvents',N'U') IS NOT NULL THEN 1 ELSE 0 END").fetchone()
            if not row or row[0]!=1:raise RuntimeError('Required SQL tables are missing')
        print(f'[OK] SQL connected: {server} / {database}')
        print('[OK] Ready to launch localhost application')
        return 0
    except Exception as exc:
        print('[NOT READY] SQL connection/schema check failed: '+str(exc),file=sys.stderr)
        print('Run INSTALL_AND_START.bat (auto-detect/repair SQL configuration).',file=sys.stderr)
        return 1

if __name__=='__main__':sys.exit(main())
