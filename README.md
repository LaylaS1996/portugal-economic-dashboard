# Portugal Economic Dashboard — International Finance

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Refresh behavior

- Clicking **Refresh source data now** invalidates Streamlit's 6-hour cache and performs new requests to Eurostat and the ECB.
- A new visit after cache expiration also retrieves current source data.
- `.github/workflows/refresh.yml` supplies an independent scheduled automated check every six hours once hosted on GitHub Actions. Review the Actions logs to prove scheduled checks, as distinct from a manual refresh.
- Source observation dates are displayed separately from request/refresh timestamps. Source releases may lag.

## Check the data

1. Click Refresh and capture a screenshot with timestamp and six indicators.
2. Download verification CSV, then open each source URL and match its latest published observation to the dashboard number and period.
3. Record two or more matched observations and note whether new data had been published.
4. Capture a screenshot of a successful scheduled run in GitHub Actions if using that workflow.
5. Never invent an observation to make a verification pass.

## Sources

Eurostat REST API: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/

ECB Exchange Rates API: https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A

Note: Euro-area currency rates are not Portugal-specific.
