# GitHub publishing checklist

1. Publish **source code and documentation**, not `.venv`, database backups, secrets, CSV datasets, user data, or prediction outputs.
2. Before `git add`, inspect `git status --short` and `git diff --cached --name-only`.
3. **Never commit `.env`** (it may contain SQL credentials). If it has ever been committed, rotate credentials and remove it from repository history.
4. Do not publish the bundled `.joblib` without checking ownership, licensing and security implications. Model checkpoints are binary artifacts; treat loading untrusted checkpoints as unsafe.
5. Keep folders: `SourceCode/` app logic, `Database/` SQL scripts, `Tests/` tests, `Documentation/` instructions, `Assets/` trusted models, `Updates/` update ZIPs, `Backups/` local backups (never GitHub).
6. Team demo: use `SourceCode/launch_large_csv.py` for large uploads. Keep local-only server binding unless network exposure is deliberately reviewed.
7. A ZIP updater **copies only approved payload paths**; this release does not alter `UPDATE_APP.bat`, `UPDATE_APP.ps1` or your SQL data.
