"""Save and read experiment records in the existing SQL Server tables."""
import json
from . import db
from .users import active_actor
from .permissions import require_role
from . import benchmark


def run_and_save(actor_id: int, algorithm: str, trials: int, progress=None):
    require_role(active_actor(actor_id)["RoleName"], ("Admin", "Researcher"))
    benchmark.validate_trials(trials)
    # Register before running, to distinguish failed and successful experiments.
    with db.connection() as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO dbo.Experiments (OwnerId, Algorithm, TrialCount, "
            "RunStatus, EnvInfo) OUTPUT INSERTED.ExperimentId "
            "VALUES (?, ?, ?, 'Running', ?)",
            (actor_id, algorithm, trials, json.dumps(benchmark.environment()))
        )
        experiment_id = int(cur.fetchone()[0])
    try:
        samples = benchmark.run_trials(algorithm, trials, progress)
        with db.connection() as con:
            cur = con.cursor()
            cur.executemany(
                "INSERT INTO dbo.Measurements "
                "(ExperimentId, OperationName, TrialIndex, DurationNs) "
                "VALUES (?, ?, ?, ?)",
                [(experiment_id, m["operation"], m["trial"], m["duration_ns"])
                 for m in samples]
            )
            cur.execute(
                "UPDATE dbo.Experiments SET RunStatus='Completed', "
                "EndedAtUtc=SYSUTCDATETIME() WHERE ExperimentId=?",
                (experiment_id,)
            )
    except Exception:
        db.execute("UPDATE dbo.Experiments SET RunStatus='Failed', "
                   "EndedAtUtc=SYSUTCDATETIME() WHERE ExperimentId=?",
                   (experiment_id,))
        raise
    return experiment_id, benchmark.summarize(samples)


def save_demo(actor_id: int, result: dict) -> None:
    require_role(active_actor(actor_id)["RoleName"], ("Admin", "Researcher"))
    db.execute(
        "INSERT INTO dbo.SecureDemoTests "
        "(UserId, Algorithm, Tampered, Passed, StatusDetail) "
        "VALUES (?, ?, ?, ?, ?)",
        (actor_id, result["algorithm"], int(result["tampered"]),
         int(result["passed"]), result["outcome"])
    )


def history(actor_id: int):
    active_actor(actor_id)  # Viewer may read, disabled users may not.
    return db.rows(
        "SELECT TOP 100 e.ExperimentId, e.Algorithm, e.TrialCount, "
        "e.RunStatus, e.StartedAtUtc, u.Username "
        "FROM dbo.Experiments AS e JOIN dbo.Users AS u "
        "ON e.OwnerId = u.UserId ORDER BY e.ExperimentId DESC"
    )


def measurements(actor_id: int, experiment_id: int):
    active_actor(actor_id)
    return db.rows(
        "SELECT OperationName, TrialIndex, DurationNs "
        "FROM dbo.Measurements WHERE ExperimentId = ? "
        "ORDER BY TrialIndex, OperationName", (experiment_id,)
    )
