"""Local, privacy-preserving, explainable IoT decision advisor.

Uses only locally supplied training metrics and gateway events. SWI-Prolog is
optional and invoked with a fixed query and fixed rules; no arbitrary goals.
Python fallback implements equivalent conservative rules without calling it Prolog.
"""
from __future__ import annotations
import json, math, shutil, subprocess
from collections import Counter
from pathlib import Path

RULES = Path(__file__).resolve().parent / 'rules' / 'security_advisor.pl'
DANGEROUS = {'device_impersonation', 'replay_attack', 'tampering', 'unauthorized_access',
             'unregistered_device', 'invalid_signature', 'rate_limit', 'replay',
             'invalid_token', 'invalid_hmac'}

def _finite_number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None

def normalize_evidence(training=None, events=None, devices=None, models=None):
    training = training if isinstance(training, dict) else {}
    held = training.get('heldout') if isinstance(training.get('heldout'), dict) else {}
    folds = training.get('folds') if isinstance(training.get('folds'), list) else []
    bounded_events = (events or [])[:5000]
    blocked = 0
    seen_attacks = Counter()
    for e in bounded_events:
        if not isinstance(e, dict):
            continue
        if str(e.get('decision', '')).upper() == 'BLOCK':
            blocked += 1
            attack = str(e.get('attack_type') or e.get('request_type') or 'unclassified').lower().replace(' ', '_')
            seen_attacks[attack] += 1
    fpr = _finite_number(held.get('false_positive_rate'))
    f1 = _finite_number(held.get('macro_f1'))
    fold_f1s = [_finite_number(x.get('macro_f1')) for x in folds[:50] if isinstance(x, dict)]
    fold_f1s = [n for n in fold_f1s if n is not None]
    device_rows = [x for x in (devices or [])[:1000] if isinstance(x, dict)]
    model_rows = [x for x in (models or [])[:1000] if isinstance(x, dict)]
    device_states = Counter(str(x.get('status','')).lower() for x in device_rows)
    # Evidence from persisted locally trained checkpoints (not an instruction).
    candidates = sum(x.get('status') == 'reviewed_candidate' for x in model_rows)
    weak_models = 0
    for model in model_rows:
        metrics = model.get('metrics') or {}
        if not isinstance(metrics, dict):continue
        this_f1 = _finite_number(metrics.get('macro_f1'))
        this_fpr = _finite_number(metrics.get('false_positive_rate'))
        if (this_f1 is not None and this_f1 < 0.80) or (this_fpr is not None and this_fpr > 0.05):
            weak_models += 1
    return {
        'active_devices': device_states.get('active', 0),
        'disabled_devices': device_states.get('disabled', 0),
        'retired_devices': device_states.get('retired', 0),
        'model_registry_count': len(model_rows),
        'reviewed_offline_candidates': candidates,
        'models_needing_quality_review': weak_models,
        'unverified_models': sum('validated' not in str(x.get('status','')).lower() for x in model_rows),
        'repeat_block_threshold': blocked >= 5,
        'unregistered_access': any('not registered' in str(x.get('reason','')).lower() for x in bounded_events if isinstance(x,dict)),
        'algorithm': str(training.get('algorithm') or 'Not trained')[:100],
        'split': str(training.get('split') or 'Unknown')[:40],
        'folds_seen': len(fold_f1s),
        'fold_spread': round(max(fold_f1s)-min(fold_f1s), 6) if len(fold_f1s)>1 else None,
        'false_positive_rate': fpr, 'macro_f1': f1,
        'dataset_truncated': bool(training.get('truncated_to_first_rows')),
        'has_training': bool(held),
        'recent_gateway_events': len(bounded_events), 'blocked_events': blocked,
        'attack_types': dict(seen_attacks.most_common(12)),
    }

def _facts(e):
    # Atom names and facts are produced only from allowlisted classifications.
    facts = []
    for key in ('has_training', 'dataset_truncated'):
        if e[key]: facts.append('flag(%s).' % key)
    if e['false_positive_rate'] is not None and e['false_positive_rate'] > 0.02: facts.append('flag(high_fpr).')
    if e['fold_spread'] is not None and e['fold_spread'] > 0.05: facts.append('flag(unstable_folds).')
    if e['blocked_events'] > 0: facts.append('flag(blocked_events).')
    if any(k in DANGEROUS for k in e['attack_types']): facts.append('flag(known_attack_types).')
    if e['unregistered_access']: facts.append('flag(unregistered_access).')
    if e['repeat_block_threshold']: facts.append('flag(repeated_blocks).')
    if e['disabled_devices'] or e['retired_devices']: facts.append('flag(device_lifecycle).')
    if e['unverified_models']: facts.append('flag(unverified_checkpoints).')
    if e['reviewed_offline_candidates']:facts.append('flag(offline_candidate).')
    if e['models_needing_quality_review']:facts.append('flag(model_quality_risk).')
    return '\n'.join(facts) + '\n'

MESSAGES = {
 'no_training': ('Training evidence missing', 'Train and validate a model locally before making any deployment decision.'),
 'high_fpr': ('False positives need attention', 'Measure false positives on representative normal traffic and revise features/thresholds before deployment.'),
 'unstable_folds': ('Fold performance inconsistent', 'Inspect individual folds and possible data leakage or temporal distribution changes.'),
 'truncated_dataset': ('Dataset coverage limited', 'Retrain using representative records; the current sample may not reflect live traffic.'),
 'blocked_incidents': ('Security events observed', 'Review blocked gateway incidents and verify reasons; a block alone does not prove ML detected an attack.'),
 'known_attack_types': ('Gateway protections active', 'Review impersonation, replay, tampering or unauthorized attempts using actual gateway event evidence.'),
 'unregistered_access': ('Unregistered device tried to access gateway', 'Review the attempted device ID. Enroll only authorized devices in LAN Lab; do not treat an unknown IP alone as proof of malice.'),
 'repeated_blocks': ('High volume of rejected requests', 'Review recent repeated blocks, rate limits and device identity; verify whether this is a test or unauthorized activity.'),
 'device_lifecycle': ('Inventory includes disabled or retired devices', 'Confirm disabled and retired device IDs remain denied; keep retired credentials revoked.'),
 'unverified_checkpoints': ('Saved checkpoints need validation', 'Do not load or deploy untrusted model files. Validate feature schema, dataset split and independent test metrics.'),
 'offline_candidate': ('Offline candidate ready for next stage', 'A model was marked reviewed but is NOT live. Collect compatible TCP/MQTT evidence and run shadow-mode tests before considering enforcement.'),
 'model_quality_risk': ('Stored model quality requires review', 'Inspect weaker saved models independently. Compare each split, fold and false-positive rate before approval.'),
 'live_unverified': ('Live ML integration not verified', 'Do not enable automatic ML blocking until a TCP/MQTT-compatible feature collector and independent validation are connected.'),
}

def _fallback_rules(e):
    flags=[]
    if not e['has_training']:flags.append('no_training')
    if e['false_positive_rate'] is not None and e['false_positive_rate']>0.02:flags.append('high_fpr')
    if e['fold_spread'] is not None and e['fold_spread']>0.05:flags.append('unstable_folds')
    if e['dataset_truncated']:flags.append('truncated_dataset')
    if e['blocked_events']>0:flags.append('blocked_incidents')
    if any(k in DANGEROUS for k in e['attack_types']):flags.append('known_attack_types')
    if e['unregistered_access']:flags.append('unregistered_access')
    if e['repeat_block_threshold']:flags.append('repeated_blocks')
    if e['disabled_devices'] or e['retired_devices']:flags.append('device_lifecycle')
    if e['unverified_models']:flags.append('unverified_checkpoints')
    if e['reviewed_offline_candidates']:flags.append('offline_candidate')
    if e['models_needing_quality_review']:flags.append('model_quality_risk')
    flags.append('live_unverified')
    return flags

def _prolog_rules(e, executable):
    # Fixed query; facts only contain hard-coded atoms. No shell invocation.
    content = _facts(e)
    import tempfile
    with tempfile.TemporaryDirectory(prefix='qs_prolog_') as td:
        facts_file = Path(td)/'facts.pl'
        facts_file.write_text(content, encoding='utf-8')
        # Fixed goal string; no user data interpolated into executable query.
        goal = "findall(R,recommendation(R),Rs),sort(Rs,Unique),forall(member(X,Unique),(write(X),nl)),halt"
        result = subprocess.run([executable, '-q', '-s', str(RULES), '-s', str(facts_file), '-g', goal],
                                capture_output=True, text=True, timeout=5, check=True)
    codes = [x.strip() for x in result.stdout.splitlines()]
    if any(code not in MESSAGES for code in codes): raise ValueError('Unexpected Prolog output')
    return codes

def analyze(training=None, events=None, prolog_executable=None, devices=None, models=None):
    evidence=normalize_evidence(training,events,devices,models)
    engine='Local rules (Python fallback; SWI-Prolog not installed)'
    error=None
    executable=prolog_executable if prolog_executable is not None else shutil.which('swipl')
    if executable and RULES.exists():
        try:
            codes=_prolog_rules(evidence,executable)
            engine='SWI-Prolog (local)'
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            error=f'Local Prolog execution unavailable: {type(exc).__name__}'
            codes=_fallback_rules(evidence)
    else:codes=_fallback_rules(evidence)
    # Prolog's `sort` orders codes; keep output deterministic across engines.
    return {'engine':engine,'evidence':evidence,
            'recommendations':[{'rule':x,'title':MESSAGES[x][0],'action':MESSAGES[x][1]} for x in sorted(set(codes))],
            'diagnostic':error, 'automated_training':False, 'live_ml_deployed':False}
