"""Offline educational content screening: no fetching, no reputation service, no browser blocking."""
import re
from urllib.parse import urlsplit
from datetime import datetime,timezone
from ipaddress import ip_address
MAX_TEXT=4000
SUSPICIOUS_WORDS=('send your password','share your otp','verify your password','enter your password','send your otp','account will be suspended','urgent bank verification','share your pin')
DANGEROUS_SCHEMES=('javascript:','data:','file:','vbscript:')
def assess_content(value):
 if not isinstance(value,str) or not value.strip():raise ValueError('Enter a message or link.')
 if len(value)>MAX_TEXT:raise ValueError('Maximum 4000 characters.')
 value=value.strip();low=value.lower();reasons=[];review=[]
 if any(x in low for x in DANGEROUS_SCHEMES):reasons.append('Unsafe URL scheme')
 if any(x in low for x in SUSPICIOUS_WORDS):reasons.append('Credential/OTP solicitation')
 if re.search(r'(?i)\b(?:https?://)?[^\s/]+\.(?:exe|scr|bat|cmd)(?:\b|[/?#])',value):review.append('Executable download pattern: investigate')
 urls=re.findall(r'(?i)https?://[^\s<>"\']+',value)
 for u in urls:
  try:
   x=urlsplit(u);host=x.hostname or ''
   if x.username or x.password:reasons.append('URL contains embedded credentials')
   if host.startswith('xn--') or '.xn--' in host:review.append('Internationalized hostname: verify')
   try:ip_address(host);review.append('Direct IP URL: verify owner and context; not automatically malicious')
   except ValueError:pass
  except ValueError:review.append('Malformed URL: verify')
 decision='BLOCK' if reasons else ('REVIEW' if review else 'UNKNOWN')
 return {'timestamp_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'), 'decision':decision,
 'reason':'; '.join(dict.fromkeys(reasons+review)) if reasons or review else 'No local risk indicator matched; website safety NOT verified',
 'device':'manual-message-test','source':'MANUAL_CONTENT_RULES','request_type':'message_or_link'}
