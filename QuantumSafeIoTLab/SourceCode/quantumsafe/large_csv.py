"""3-GiB CSV acceptance with bounded-memory preparation for local ML.

Entire file is scanned for representative random sampling; training still
runs on a bounded sample until an out-of-core trainer is implemented.
"""
from __future__ import annotations
import os
import shutil
from pathlib import Path
import numpy as np
import pandas as pd

MAX_CSV_BYTES = 3 * 1024 ** 3
SAMPLE_ROWS = 20000


def checked_csv(path):
    p = Path(path).expanduser().resolve()
    if not p.is_file() or p.suffix.lower() != '.csv':
        raise ValueError('Select an existing .csv file stored on this PC.')
    size = p.stat().st_size
    if not 0 < size <= MAX_CSV_BYTES:
        raise ValueError('CSV must be non-empty and no larger than 3 GiB (3,221,225,472 bytes).')
    return p


def headers(path):
    return pd.read_csv(checked_csv(path), nrows=0).columns.tolist()


def stage_upload(upload, target):
    """Copy uploaded bytes in chunks; avoid upload.getvalue() full-size duplication.

    Streamlit may already buffer uploads in RAM. For 3GiB prefer local path.
    """
    if not upload.name.lower().endswith('.csv') or upload.size > MAX_CSV_BYTES:
        raise ValueError('Only CSV uploads up to 3 GiB are supported.')
    target = Path(target)
    upload.seek(0)
    with target.open('wb') as dst:
        shutil.copyfileobj(upload, dst, length=4 * 1024 * 1024)
    return checked_csv(target)


def representative_sample(path, features, label, max_rows=SAMPLE_ROWS, seed=42):
    """Reservoir-like random-priority sample across the FULL CSV, not first N rows.

    Avoids data leakage in *selection*, but random row sampling cannot fix
    temporal/device correlation or class imbalance; validate deployment separately.
    """
    p = checked_csv(path)
    cols = list(dict.fromkeys([*features, label]))
    if not features or label in features or len(features) > 30:
        raise ValueError('Choose 1–30 features excluding the target label')
    exists = headers(p)
    if any(col not in exists for col in cols):
        raise ValueError('Missing columns: ' + ', '.join(col for col in cols if col not in exists))
    rng = np.random.default_rng(seed)
    kept = None
    scanned = 0
    for chunk in pd.read_csv(p, usecols=cols, chunksize=20000, low_memory=False):
        if chunk.empty: continue
        scanned += len(chunk)
        chunk = chunk.copy()
        chunk['_qs_sample_priority'] = rng.random(len(chunk))
        if kept is None:
            kept = chunk
        else:
            kept = pd.concat([kept, chunk], ignore_index=True)
        if len(kept) > max_rows:
            kept = kept.nlargest(max_rows, '_qs_sample_priority').reset_index(drop=True)
    if kept is None or kept.empty:
        raise ValueError('CSV contains no data rows')
    kept = kept.drop(columns=['_qs_sample_priority'])
    return {'sample': kept, 'total_rows': scanned,
            'sampled_rows': len(kept), 'source_bytes': p.stat().st_size,
            'random_seed': seed, 'source_file': p.name,
            'sample_method': 'uniform random-priority sample across all parsed rows'}
