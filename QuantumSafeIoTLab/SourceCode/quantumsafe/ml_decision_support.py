"""Deterministic, evidence-linked advice. No invented metrics."""

def summarize_training(result):
    """Return only metrics and non-sensitive schema metadata, never model objects or raw CSV."""
    allowed=('algorithm','split','folds','heldout','classes','training_rows','test_rows','sample_rows','truncated_to_first_rows','features','seed','data_sha256')
    return {key:result[key] for key in allowed if key in result}

def practical_guidance(evidence):
    held=evidence.get('heldout') or {}
    folds=evidence.get('folds') or []
    advice=[f"**{evidence.get('algorithm','Model')} ({evidence.get('split','unknown split')})** — held-out Macro-F1: {held.get('macro_f1','not measured')}; accuracy: {held.get('accuracy','not measured')}."]
    fpr=held.get('false_positive_rate')
    if isinstance(fpr,(int,float)):
        advice.append(f'False-positive rate: {fpr:.3%}. Measure this against actual benign device traffic before enabling automatic blocks.')
    if len(folds)>1:
        vals=[f.get('macro_f1') for f in folds if isinstance(f.get('macro_f1'),(int,float))]
        if len(vals)>1:
            spread=max(vals)-min(vals)
            advice.append(f'Across {len(vals)} validation folds, Macro-F1 range is {spread:.4f}. '+('Inspect unstable folds and class imbalance.' if spread>0.05 else 'Fold results are relatively consistent on this sample.'))
    if evidence.get('truncated_to_first_rows'):
        advice.append('Training used a limited first-rows sample; rerun with a representative, time-aware dataset before deployment.')
    advice.append('**Live status: NOT DEPLOYED.** HTTP gateway events cannot be passed into TCP/MQTT models without a verified matching feature collector. Administrator approval and offline validation are required.')
    return '\n\n'.join(advice)
