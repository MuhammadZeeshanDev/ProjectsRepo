"""Streaming CSV screening for supervised IoT IDS training; no full-file RAM load."""
from __future__ import annotations
import csv
import hashlib
import heapq
import math
from pathlib import Path
import numpy as np
import pandas as pd

LABEL_NAMES = ('Attack_label', 'attack_label', 'Label', 'label', 'is_attack',
               'attack_type', 'Attack_type', 'class', 'Class', 'target', 'Target', 'intrusion')
HIGH_RISK_MARKERS = ('timestamp', 'frame.time', 'time_stamp', 'source_ip',
                     'destination_ip', 'ip.src', 'ip.dst', 'host', 'raw_payload', 'password',
                     'token', 'secret', 'session_id', 'attack_label', 'attack_type', 'label')


def inspect_headers(path):
    p = Path(path).expanduser().resolve(strict=True)
    if not p.is_file() or p.suffix.lower() != '.csv':
        raise ValueError('Pass an existing local .csv file, not a ZIP or an uploaded file.')
    with p.open('r', encoding='utf-8-sig', newline='') as fh:
        cols = next(csv.reader(fh))
    if not cols or len(cols) != len(set(cols)):
        raise ValueError('Missing or duplicate CSV column headers.')
    return p, cols


def pick_label(cols, explicit=None):
    if explicit:
        if explicit not in cols: raise ValueError(f'Label {explicit!r} not found. Columns: {cols[:50]}')
        return explicit
    for name in LABEL_NAMES:
        if name in cols: return name
    raise ValueError('No recognized attack/benign label. Set --label to the exact supervised target column. Unlabeled CSV cannot train a classifier.')


def auto_features(cols, label):
    out=[]
    for col in cols:
        k=col.casefold().replace('-', '_').replace(' ', '_')
        if col == label or k=='mqtt.protoname' or k=='id' or k.endswith('_id') or k.startswith('id_') or any(word in k for word in HIGH_RISK_MARKERS): continue
        out.append(col)
    if not out: raise ValueError('No safe candidate columns; supply --features explicitly after verifying leakage risk.')
    return out[:100]


def _hash(path, block=4*1024*1024):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(block), b''): h.update(chunk)
    return h.hexdigest()


def scan_csv(path, *, label=None, features=None, max_rows=30000, seed=42, chunksize=10000,
             normal=None, binary=False, hash_data=True):
    """Uniform-priority bounded reservoir with class-aware minimum retention.

    Works with large local CSV files of arbitrary size subject to disk, runtime and
    file parse limits. No claim of training on every row; returns scanned/sampled counts.
    """
    p, cols=inspect_headers(path)
    target=pick_label(cols,label)
    feats = list(features) if features is not None else auto_features(cols,target)
    if not 1 <= len(feats) <= 100 or target in feats or len(set(feats)) != len(feats):
        raise ValueError('Choose 1–100 distinct non-label features.')
    if set(feats)-set(cols):raise ValueError('Features missing from CSV: '+str(sorted(set(feats)-set(cols))))
    if max_rows<200 or max_rows>500000:raise ValueError('--max-rows must be 200 to 500000; choose according to RAM.')
    if chunksize<100 or chunksize>50000:raise ValueError('Invalid chunk size.')
    # Uniform random-priority reservoir for general population plus a small
    # per-class minimum, so minority attacks are not discarded by chance.
    # Bounded RAM: roughly max_rows + 100 * max(2,max_rows//1000) dictionaries.
    min_class_cap=min(50,max(2,max_rows//100))
    rng=np.random.default_rng(seed)
    global_heap=[]; class_heaps={};counts={};full_count=0;missing_labels=0
    row_id=0
    for chunk in pd.read_csv(p, usecols=list(dict.fromkeys([*feats,target])),
                             chunksize=chunksize, low_memory=False, on_bad_lines='error'):
        full_count+=len(chunk)
        if chunk.empty:continue
        labels=chunk[target].astype('string').str.strip()
        if binary:
            if normal is None: raise ValueError('Binary mode requires --normal-label, e.g. 0 or Normal')
            labels = labels.map(lambda x: pd.NA if pd.isna(x) else ('normal' if str(x).casefold()==str(normal).strip().casefold() else 'attack'))
        valid=labels.notna() & labels.ne('')
        missing_labels+=int((~valid).sum())
        records=chunk.loc[valid,feats].to_dict('records')
        targets=labels.loc[valid].tolist()
        for row,cls in zip(records,targets):
            cls=str(cls);counts[cls]=counts.get(cls,0)+1
            if len(counts)>100:raise ValueError(f'Found >100 distinct target classes; wrong label column? Found examples: {list(counts)[:15]}')
            row_id+=1; item=(float(rng.random()),row_id,cls,row)
            if len(global_heap)<max_rows:heapq.heappush(global_heap,item)
            elif item[0]>global_heap[0][0]:heapq.heapreplace(global_heap,item)
            bucket=class_heaps.setdefault(cls,[])
            if len(bucket)<min_class_cap:heapq.heappush(bucket,item)
            elif item[0]>bucket[0][0]:heapq.heapreplace(bucket,item)
    if len(counts)<2:raise ValueError(f'Target {target!r} has {len(counts)} class(es). Need 2+ classes. Check --label and --normal-label.')
    forced=[]
    for cls,bucket in sorted(class_heaps.items()):forced.extend(bucket)
    selected_ids={x[1] for x in forced}
    global_rest=[x for x in global_heap if x[1] not in selected_ids]
    global_rest.sort(key=lambda x:(-x[0],x[1]))
    selected=forced+global_rest[:max(0,max_rows-len(forced))]
    # Sort by input record order for stable, human-reviewable saved sample.
    selected.sort(key=lambda x:x[1])
    selection=[(item[2],item[3]) for item in selected]
    frame=pd.DataFrame([row for _,row in selection],columns=feats)
    frame[target]=[cls for cls,_ in selection]
    return {'frame':frame, 'target':target, 'features':feats,
            'source_path':str(p), 'source_bytes':p.stat().st_size,
            'source_sha256':_hash(p) if hash_data else None,
            'rows_seen':full_count,'missing_label_rows':missing_labels,
            'sampled_rows':len(frame),'source_class_counts':counts,
            'sample_class_counts':frame[target].value_counts().to_dict(),
            'seed':seed,'method':'streaming random-priority, stratified minimum; validation is on sampled rows'}
