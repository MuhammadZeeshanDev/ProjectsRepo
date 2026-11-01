"""Conservative educational message/URL policy for manually submitted content.
Not a browser extension, malware scanner, reputation service, or ML model.
"""
import re
from urllib.parse import urlsplit
from datetime import datetime, timezone

MAX_TEXT=4000
SUSPICIOUS_WORDS=('send your password','share your otp','verify your password',
 'enter your password','send your otp','account will be suspended',
 'urgent bank verification','share your pin')
DANGEROUS_SCHEMES=('javascript:','data:','file:','vbscript:')

def assess_content(value):
    if not isinstance(value,str) or not value.strip():
        raise ValueError('Enter a message or link to test.')
    if len(value)>MAX_TEXT:raise ValueError('Input is too long (maximum 4000 characters).')
    original=value.strip()
    low=original.lower()
    reasons=[]
    if any(x in low for x in DANGEROUS_SCHEMES):
        reasons.append('Potentially unsafe URL scheme')
    if any(x in low for x in SUSPICIOUS_WORDS):
        reasons.append('Credential or OTP solicitation pattern')
    if re.search(r'(?i)\b(?:https?://)?[^\s/]+\.(?:zip|exe|scr|bat|cmd)(?:\b|[/?#])',original):
        reasons.append('Potential executable/archive link pattern (review required)')
    # Only parse an actual URL; never fetch, click, or open it.
    urls=re.findall(r'(?i)https?://[^\s<>"\']+',original)
    for u in urls:
        try:
            parsed=urlsplit(u)
            host=(parsed.hostname or '').lower()
            if parsed.username or parsed.password:reasons.append('URL embeds login information')
            if host.startswith('xn--') or '.xn--' in host:reasons.append('Internationalized hostname requires review')
            if host.replace('.','').isdigit() and host:reasons.append('Numeric IP-style hostname requires review')
        except ValueError:reasons.append('Malformed URL')
    return {'timestamp_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
      'decision':'BLOCK' if reasons else 'ALLOW',
      'reason':'; '.join(dict.fromkeys(reasons)) if reasons else 'No configured suspicious patterns detected',
      'device':'manual-message-test','source':'MANUAL_CONTENT_RULES','request_type':'message_or_link'}
