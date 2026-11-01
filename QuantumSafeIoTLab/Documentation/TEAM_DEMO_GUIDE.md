# QuantumSafe IoT Lab — Beginner Team Walkthrough (v0.4.0)

## What and why
IoT = Internet of Things (cameras, sensors, routers). Our goal is a **safe, local, software-only lab** for demonstrating device requests, gateway decisions, stored security events and offline machine-learning predictions. This is an educational prototype, **not** an internet-facing firewall or real-device intrusion detector.

## Architecture (two distinct paths)

```
CCTV / Router / Sensor simulator
    -> Local HTTP gateway (127.0.0.1)
    -> rule-based ALLOW or BLOCK
    -> SQL Server: dbo.VirtualGatewayEvents
    -> Virtual Gateway + Home Dashboard

Edge-IIoTset CSV
    -> stored preprocessing (10 columns -> 11 model inputs)
    -> saved SA-HFS v3 Random Forest
    -> normal (0) / attack (1) predictions
    -> SQL Server: dbo.MLPredictionRuns (summary only)
    -> ML Lab + Home Dashboard
```

## 8-minute demo script (speak simply)
1. **1 min: Problem.** IoT devices send requests. We need a safe place to learn how suspicious requests look.
2. **1 min: Tools.** Python is the logic, Streamlit is the interface, SQL Server is the record book, Random Forest is the trained classifier.
3. **2 min: Gateway.** Open Virtual Gateway, initialize SQL event table if needed, start the local gateway. Send a normal CCTV request, then an unauthorized request. Explain ALLOW and BLOCK.
4. **1 min: Monitoring.** Show event counts and history; events in SQL persist across restarts.
5. **2 min: ML.** Open ML Lab, initialize SQL ML history if needed, upload the compatible Edge-IIoTset CSV, run the already-trained model. Explain that model predictions are **offline** and not connected to gateway blocking.
6. **1 min: Dashboard.** Show both summaries separately. Open SQL history; point to the two tables.

## SQL Server tables
- `dbo.VirtualGatewayEvents`: time, device ID, allow/block decision, reason, request source/type.
- `dbo.MLPredictionRuns`: run time, model, number of records, predicted normal/attack, optional exploratory metrics. **No raw dataset or full predictions are stored in SQL.**

## Important limitations
- Gateway requests are local simulation, not sniffed real traffic.
- Gateway decisions are rule-based; ML is not doing real-time gateway detection.
- A 99.90% score on an arbitrary CSV is exploratory and may include training overlap.
- Model requires exact trained features; do not substitute arbitrary synthetic data.
- The output predictions CSV is stored in a temporary local path and may be removed by OS cleanup. Move it to a safe location if you need it.

## What the team can explain
- **Why:** learn IoT security and build a reproducible demo.
- **How:** simulated traffic + rules + SQL logging; separate CSV + trained ML inference.
- **What next:** validate on genuinely unseen data, design trusted live feature extraction, add tests and stronger security before any real deployment.
