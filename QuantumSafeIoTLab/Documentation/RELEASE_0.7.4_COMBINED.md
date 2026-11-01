# QuantumSafe combined next-development release v0.7.4

Contains the next two planned milestones, not the previous cumulative updates:
- v0.7.3: SQL Server incident detail columns (source IP, attack type, affected component, precaution); non-destructive schema extension.
- v0.7.4: device-wise observed activity report and detailed blocked-incident view.

Requires prior v0.7.2 installation. Does NOT install 0.7.0/0.7.1/0.7.2.

Important limitations: source IP is 127.0.0.1 for loopback requests, not an independently authenticated attacker identity. Device online/connected state is NOT proven. Browser audio autoplay may be blocked. This update does not implement Windows native notifications, real device-to-gateway ML-KEM sessions, model training, or Prolog.

To test: start gateway, run independent attacker console, check detailed blocked event and device-wise report, then inspect SQL VirtualGatewayEvents for new columns. Existing rows have NULL in new columns. SQL backup recommended before schema changes.
