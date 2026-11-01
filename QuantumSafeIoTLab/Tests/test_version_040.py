from pathlib import Path
import ast
root=Path(__file__).resolve().parents[1]
assert (root/'SourceCode/quantumsafe/version.py').is_file()
for p in ['SourceCode/app.py','SourceCode/quantumsafe/ui/dashboard.py','SourceCode/quantumsafe/ui/ml_lab.py','SourceCode/quantumsafe/ml_run_store.py','SourceCode/quantumsafe/ui/start_here.py']:
    ast.parse((root/p).read_text(encoding='utf-8'))
print('v0.4.0 syntax smoke test passed')
