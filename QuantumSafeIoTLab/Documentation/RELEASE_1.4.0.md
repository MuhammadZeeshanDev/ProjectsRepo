# QuantumSafe v1.4.0 — Offline Local AI + Prolog

Install after v1.3.0 via UPDATE_APP.bat (one ZIP at a time).

- ML Lab > AI & improvement now uses local evidence from the current training session and in-memory gateway events.
- No OpenAI/API key, internet access, cloud storage or external model is required.
- SWI-Prolog (`swipl`) is optional. Install it locally and ensure `swipl` is on Windows PATH, then restart the app to activate actual Prolog execution. If absent, a clearly labeled Python implementation of the same decision rules runs offline. No automatic download.
- Prolog code: SourceCode/quantumsafe/rules/security_advisor.pl. Administrator can inspect/edit rule file; changes require review and application restart.
- The local advisor is an explainable rule engine, not a local generative chatbot/LLM. To add an actual locally hosted LLM in a later release would require a runtime (e.g. Ollama) and model weights, with machine-appropriate RAM/VRAM, and explicit data access permissions.
- Training metrics exist in current Streamlit session; gateway events are last 200 in-memory events. Models in registry are not unpickled or executed.
- No SQL server schema changes, no outgoing network calls, and no automatic model deployment.
- v1.3.0 administrator/operator role enforcement is preserved; only AI page is replaced.
