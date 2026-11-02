"""Evidence-grounded AI advisor. Remote LLM is optional, never silently simulated."""
import json, os, urllib.request, urllib.error
from . import research_catalog as catalog
def build_context(version,table,model=None,split=None,fold=None,balancing=None):
    records=catalog.load(version,table)
    rows=catalog.select(records,model,split,fold,balancing)
    keys=['Model','Split','Fold','Balancing','Method','Macro_F1','FPR','F1','Accuracy','TN','FP','FN','TP']
    evidence=[{k:r[k] for k in keys if k in r} for r in rows[:12]]
    return {'version':version,'table':table,'source_sha256':catalog.file_sha256(version,table),'count':len(rows),'records':evidence,'mean_macro_f1':catalog.report(rows,'Macro_F1')['average'],'mean_fpr':catalog.report(rows,'FPR')['average']}
def local_advice(ctx):
    if not ctx['count']:return 'No matching recorded experiments. Change the selection; no accuracy claims can be made.'
    text=f"Found {ctx['count']} recorded experiments from {ctx['version']} / {ctx['table']} (SHA256 {ctx['source_sha256'][:16]}…)."
    if ctx['mean_macro_f1'] is not None:text+=f" Mean historical macro-F1: {ctx['mean_macro_f1']:.5f}."
    if ctx['mean_fpr'] is not None:text+=f" Mean historical false-positive rate: {ctx['mean_fpr']:.5f}."
    text+=' Compare folds separately, examine false positives and source split, and validate held-out results before selecting deployment candidate. This is rule-generated guidance, not generative AI or a live prediction.'
    return text
def ask_llm(ctx,question,api_key,model='gpt-4.1-mini'):
    if not api_key or not api_key.strip():raise ValueError('API key is required for genuine remote AI answers.')
    if not question.strip():raise ValueError('Enter a question.')
    import re
    if not re.fullmatch(r'[A-Za-z0-9_.-]{2,90}',model):raise ValueError('Invalid model identifier')
    payload={'model':model,'messages':[{'role':'system','content':'You are a defensive ML research advisor. Answer only from supplied evidence; do not invent experiment metrics or imply that models are deployed. Clearly identify uncertainty. Never request passwords, security keys or execute code.'},{'role':'user','content':'Verified local model-training metrics (no raw examples): '+json.dumps(ctx,ensure_ascii=False)[:13000]+'\nQuestion: '+question[:2000]}],'temperature':0.2,'max_tokens':650}
    req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+api_key,'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=25) as response:data=json.load(response)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'AI API returned HTTP {e.code}; verify key, model access, and billing.') from None
    except (urllib.error.URLError,TimeoutError) as e:raise RuntimeError('AI API unavailable: '+str(e)) from None
    try:return data['choices'][0]['message']['content']
    except (KeyError,IndexError,TypeError):raise RuntimeError('Unrecognized AI API response')
