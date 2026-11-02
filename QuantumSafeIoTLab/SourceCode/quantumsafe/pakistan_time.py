"""Display-only Pakistan time conversion. Keep storage timestamps in UTC."""
from datetime import datetime, timezone, timedelta
PKT = timezone(timedelta(hours=5), name='PKT')

def display(value):
    if value is None or value == '':
        return ''
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PKT).strftime('%d-%m-%Y %H:%M:%S')

def localize_rows(rows):
    return [dict(row, **{'Date / Time (Islamabad PKT)': display(row.get('timestamp_utc'))}) for row in rows]
