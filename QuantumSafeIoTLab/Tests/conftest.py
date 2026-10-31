"""Make the small Python modules importable when running pytest at project root."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "SourceCode"))
