"""Minimal SQL Server metadata store; no raw CSV or full predictions stored."""
from .db import connection

def initialize():
    with connection() as con:
        con.cursor().execute("""
        IF OBJECT_ID(N'dbo.MLPredictionRuns',N'U') IS NULL
        BEGIN
            CREATE TABLE dbo.MLPredictionRuns (
                RunId BIGINT IDENTITY(1,1) PRIMARY KEY,
                CreatedUtc DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
                ModelName NVARCHAR(120) NOT NULL,
                RowsProcessed BIGINT NOT NULL,
                NormalCount BIGINT NOT NULL,
                AttackCount BIGINT NOT NULL,
                Accuracy FLOAT NULL,
                PrecisionAttack FLOAT NULL,
                RecallAttack FLOAT NULL,
                F1Attack FLOAT NULL,
                SourceKind NVARCHAR(30) NOT NULL,
                CONSTRAINT CK_ML_Rows CHECK (RowsProcessed >= 0 AND NormalCount >= 0 AND AttackCount >= 0)
            );
        END
        """)
    return True

def is_initialized():
    with connection() as con:
        cur=con.cursor()
        cur.execute("SELECT CASE WHEN OBJECT_ID(N'dbo.MLPredictionRuns',N'U') IS NULL THEN 0 ELSE 1 END")
        return bool(cur.fetchone()[0])

def insert_run(result):
    if not is_initialized(): raise RuntimeError('ML history table is not initialized')
    metrics=result.get('metrics') or {}
    with connection() as con:
        con.cursor().execute("""
        INSERT INTO dbo.MLPredictionRuns
        (ModelName,RowsProcessed,NormalCount,AttackCount,Accuracy,PrecisionAttack,RecallAttack,F1Attack,SourceKind)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,'SA-HFS v3 Random Forest',int(result['rows']),int(result['counts'].get(0,0)),
        int(result['counts'].get(1,0)),metrics.get('Accuracy'),metrics.get('Precision (attack=1)'),
        metrics.get('Recall (attack=1)'),metrics.get('F1 (attack=1)'), 'offline_csv')

def recent_runs(limit=50):
    limit=max(1,min(int(limit),200))
    with connection() as con:
        cur=con.cursor()
        cur.execute(f"""SELECT TOP ({limit}) RunId,CreatedUtc,ModelName,RowsProcessed,NormalCount,AttackCount,
            Accuracy,PrecisionAttack,RecallAttack,F1Attack,SourceKind
            FROM dbo.MLPredictionRuns ORDER BY RunId DESC""")
        return [dict(run_id=int(r[0]),created_utc=str(r[1]),model=r[2],rows_processed=int(r[3]),
            normal_count=int(r[4]),attack_count=int(r[5]),accuracy=r[6],precision=r[7],recall=r[8],f1=r[9],source=r[10]) for r in cur.fetchall()]
