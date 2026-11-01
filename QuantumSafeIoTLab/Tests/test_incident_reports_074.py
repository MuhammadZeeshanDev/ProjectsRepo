from quantumsafe.incident_reports import device_summary, incident_summary

def test_device_counts():
    events=[{'device':'cam','decision':'BLOCK','reason':'Invalid token','timestamp_utc':'2026-01-01T00:00:00Z'},
            {'device':'cam','decision':'ALLOW','timestamp_utc':'2026-01-01T00:00:01Z'}]
    row=device_summary(events,{'cam':'Camera'})[0]
    assert row['Blocked']==1 and row['Allowed']==1
    assert row['Connection status'].startswith('Not verified')
    assert incident_summary(events)['blocked']==1
