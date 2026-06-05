# NCB Credit Risk Manager Platform V2.3 - CRO / ICAAP Edition

This Streamlit package upgrades the Techcombank Credit Risk Analytics prototype into an NCB Credit Risk Manager / CRO Office demo.

## New in V2.3
- ICAAP Lite: RWA, stress loss, post-stress CAR and capital buffer status.
- Recovery Plan: automatic trigger/action table for NPL, Stage 2, CAR, concentration and EWS escalation.
- Credit Strategy Simulator: compare sector growth strategies by EAD, ECL, RWA and RAROC.
- Collateral Haircut Engine: base/adverse collateral valuation and shortfall analysis.
- Risk Committee Pack: downloadable text pack for committee discussion.

## Existing V2.2 features retained
- Executive dashboard
- Portfolio quality
- Risk appetite
- Concentration risk
- Policy rule engine
- Limit monitoring
- Single customer view
- Credit memo generator
- EWS + external alerts
- IFRS9 and stress testing
- Basel capital lite
- Watchlist and action tracker
- Board pack export
- Model governance
- NCB interview mode

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud
Main file path: `app.py`
