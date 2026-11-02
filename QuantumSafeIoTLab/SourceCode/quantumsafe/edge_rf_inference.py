"""Offline inference with the bundled, trusted Edge-IIoTset SA-HFS v3 RF checkpoint."""
from pathlib import Path
import hashlib
import io

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / 'Assets' / 'EdgeIIoT_RF_70_30' / 'SA_HFS_v3__Random_Forest_Model.joblib'
MAX_BYTES = 3 * 1024 * 1024 * 1024


def load_checkpoint():
    import joblib
    import streamlit as st
    if not MODEL_PATH.is_file():
        raise ValueError('Bundled model missing. Reapply v0.3.1 update.')
    digest = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError('Bundled model checksum mismatch. Model loading refused.')
    return _cached_checkpoint(digest)


def _validate_checkpoint(c):
    if not isinstance(c, dict) or not {'model','preprocessor','features'}.issubset(c):
        raise ValueError('Invalid checkpoint structure')
    if len(c['features']) != 10 or c['model'].n_features_in_ != 11:
        raise ValueError('Unexpected checkpoint feature dimensions')
    if not hasattr(c['preprocessor'], 'transform'):
        raise ValueError('Missing fitted preprocessor')
    return c


def _cached_checkpoint(digest):
    import joblib
    return _validate_checkpoint(joblib.load(MODEL_PATH))


def predict_csv(raw: bytes, max_rows=10000):
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('Upload a nonempty CSV no larger than 3 GiB; for large files use the local-path streaming tester.')
    checkpoint = load_checkpoint()
    cols = list(checkpoint['features'])
    df = pd.read_csv(io.BytesIO(raw), nrows=max_rows, low_memory=False)
    if df.empty:
        raise ValueError('CSV has no records.')
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(missing))
    x = df[cols].copy()
    numeric = [col for col in cols if col != 'mqtt.protoname']
    for col in numeric:
        original = x[col]
        converted = pd.to_numeric(original, errors='coerce')
        invalid = original.notna() & converted.isna()
        if invalid.any():
            raise ValueError(f'Column {col}: {int(invalid.sum())} nonnumeric values. Correct CSV before prediction.')
        x[col] = converted
    x['mqtt.protoname'] = x['mqtt.protoname'].fillna('__ZERO__').astype(str)
    # The original notebook may have applied additional normalization; do not silently claim equivalence.
    processed = checkpoint['preprocessor'].transform(x)
    if processed.shape[1] != checkpoint['model'].n_features_in_:
        raise ValueError('Processed feature count does not match classifier.')
    predictions = checkpoint['model'].predict(processed)
    result = df.copy()
    result['QuantumSafe_Prediction'] = predictions
    metrics = None
    if 'Attack_label' in df:
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
        truth = pd.to_numeric(df['Attack_label'], errors='coerce')
        if truth.notna().all() and truth.isin([0, 1]).all():
            metrics = {
                'Accuracy': float(accuracy_score(truth, predictions)),
                'Precision (attack=1)': float(precision_score(truth, predictions, zero_division=0)),
                'Recall (attack=1)': float(recall_score(truth, predictions, zero_division=0)),
                'F1 (attack=1)': float(f1_score(truth, predictions, zero_division=0)),
                'Confusion matrix': confusion_matrix(truth, predictions, labels=[0,1]).tolist(),
            }
    return result, metrics

EXPECTED_SHA256 = '962c650ffc6894b49808310b8928d06c14bc757c3ef3f8f2f8c476cca0a0fb6d'


# Disk-based processing: handles large local CSV files without browser upload limits.
def predict_local_csv(path, chunk_size=10000, progress=None):
    import csv
    import tempfile
    from sklearn.metrics import confusion_matrix
    import numpy as np
    checkpoint = load_checkpoint()
    path = Path(path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != '.csv':
        raise ValueError('Select an existing .csv file on this computer.')
    if path.stat().st_size == 0 or path.stat().st_size > MAX_BYTES:
        raise ValueError('CSV must be non-empty and no larger than 3 GiB.')
    cols = list(checkpoint['features'])
    output = tempfile.NamedTemporaryFile(prefix='quantumsafe_predictions_', suffix='.csv', delete=False)
    output.close()
    output_path = Path(output.name)
    total = 0
    counts = {0: 0, 1: 0}
    confusion = np.zeros((2,2), dtype=np.int64)
    evaluated = 0
    label_present = None
    preview = []
    try:
        for chunk in pd.read_csv(path, chunksize=chunk_size, low_memory=False):
            if chunk.empty:
                continue
            missing = [col for col in cols if col not in chunk.columns]
            if missing:
                raise ValueError('Missing required columns: ' + ', '.join(missing))
            x = chunk[cols].copy()
            for col in cols:
                if col != 'mqtt.protoname':
                    x[col] = pd.to_numeric(x[col], errors='coerce')
            x['mqtt.protoname'] = x['mqtt.protoname'].fillna('__ZERO__').astype(str)
            processed = checkpoint['preprocessor'].transform(x)
            if processed.shape[1] != checkpoint['model'].n_features_in_:
                raise ValueError('Processed feature count mismatch.')
            predictions = checkpoint['model'].predict(processed)
            chunk = chunk.copy()
            chunk['QuantumSafe_Prediction'] = predictions
            chunk.to_csv(output_path, mode='a', header=(total == 0), index=False)
            if sum(len(p) for p in preview) < 100:
                remaining = 100 - sum(len(p) for p in preview)
                preview.append(chunk.head(remaining).copy())
            total += len(chunk)
            for label in (0,1):
                counts[label] += int((predictions == label).sum())
            if label_present is None:
                label_present = 'Attack_label' in chunk
            if label_present:
                truth = pd.to_numeric(chunk['Attack_label'], errors='coerce')
                valid = truth.isin([0,1])
                if valid.any():
                    confusion += confusion_matrix(truth[valid].astype(int), predictions[valid], labels=[0,1])
                    evaluated += int(valid.sum())
            if progress:
                progress(total)
        if not total:
            raise ValueError('CSV contains no data rows.')
        tn, fp, fn, tp = map(int, (confusion[0,0], confusion[0,1], confusion[1,0], confusion[1,1]))
        metrics = None
        if evaluated:
            metrics = {
                'Accuracy': (tp+tn)/evaluated,
                'Precision (attack=1)': tp/(tp+fp) if tp+fp else 0.0,
                'Recall (attack=1)': tp/(tp+fn) if tp+fn else 0.0,
                'F1 (attack=1)': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0,
                'Confusion matrix': confusion.tolist(),
                'Evaluated labeled rows': evaluated,
            }
        return {'rows':total, 'counts':counts, 'metrics':metrics,
                'preview':pd.concat(preview, ignore_index=True).head(100) if preview else pd.DataFrame(),
                'output_path':str(output_path)}
    except Exception:
        output_path.unlink(missing_ok=True)
        raise
