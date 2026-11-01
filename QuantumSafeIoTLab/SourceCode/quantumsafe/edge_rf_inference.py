"""Offline inference with the bundled, trusted Edge-IIoTset SA-HFS v3 RF checkpoint."""
from pathlib import Path
import hashlib
import io

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / 'Assets' / 'EdgeIIoT_RF_70_30' / 'SA_HFS_v3__Random_Forest_Model.joblib'
MAX_BYTES = 60 * 1024 * 1024


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
        raise ValueError('Upload a nonempty CSV smaller than 60 MB.')
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
