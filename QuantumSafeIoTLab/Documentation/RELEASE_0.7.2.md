# v0.7.2 — Device-specific tests, clearer link verdicts, browser alarm

- Separate admin diagnostics for CCTV, router and temperature sensor; independent PC B per-device tests.
- Gateway events include attack_type, affected_component and precaution (in-memory and HTTP response). Existing SQL schema may not persist these new fields; migration required later.
- Browser alarm and notification permission controls added to live alerts. Browser autoplay, iframe permissions, muted tabs and OS notification policy can prevent sound or notifications; click Enable sound & notifications and Test alarm. No guaranteed OS-wide alarm.
- Offline URL checker returns BLOCK, REVIEW or UNKNOWN. It does not visit sites or use reputation services. A normal website URL cannot be certified safe. IP addresses alone do not establish maliciousness.
- Tests are controlled localhost application requests, not physical IoT attacks or network-wide firewall.
- Next: persistent event IDs and notification delivery, true per-device credentials/session lifecycle, SQL incident schema migration, then ML/Prolog integrations.
