import io
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Portugal | Economic Dashboard", page_icon="🇵🇹", layout="wide")

EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
ECB = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"

SERIES = {
    "Real GDP growth": dict(dataset="namq_10_gdp", filters={"geo":"PT", "unit":"CLV_PCH_PRE", "na_item":"B1G", "s_adj":"SCA", "freq":"Q"}, unit="% QoQ", freq="Quarterly", note="Real GDP, chain-linked volume, seasonally and calendar adjusted; percentage change from preceding quarter."),
    "Inflation (HICP)": dict(dataset="prc_hicp_manr", filters={"geo":"PT", "coicop":"CP00", "unit":"RCH_A", "freq":"M"}, unit="% YoY", freq="Monthly", note="All-items harmonised consumer price index, reported annual percentage rate of change."),
    "Unemployment": dict(dataset="une_rt_m", filters={"geo":"PT", "s_adj":"SA", "age":"TOTAL", "sex":"T", "unit":"PC_ACT", "freq":"M"}, unit="% labor force", freq="Monthly", note="Seasonally adjusted unemployment rate, total ages and both sexes."),
    "Government debt/GDP": dict(dataset="gov_10dd_edpt1", filters={"geo":"PT", "na_item":"GD", "unit":"PC_GDP", "sector":"S13", "freq":"A"}, unit="% of GDP", freq="Annual", note="General government consolidated gross debt as share of GDP."),
    "10-year government yield": dict(dataset="irt_lt_mcby_m", filters={"geo":"PT", "freq":"M"}, unit="% per annum", freq="Monthly", note="Long-term government bond yield used for convergence purposes; monthly percent."),
}


def extract_jsonstat(payload):
    """Extract a filtered, one-series JSON-stat result using declared time dimension."""
    dims = payload["id"]
    sizes = payload["size"]
    categories = payload["dimension"]
    if "time" not in dims:
        raise ValueError(f"No time dimension in API result: {dims}")
    # Eurostat may still return multiple dimension categories after filtering.
    # Fail clearly rather than silently choosing a potentially wrong series.
    remaining = {d: sizes[i] for i, d in enumerate(dims) if d != "time" and sizes[i] != 1}
    if remaining:
        raise ValueError(f"Multiple categories returned: {remaining}. Add a filter to select a single series.")
    time_idx = dims.index("time")
    time_cat = categories["time"]["category"]["index"]
    if isinstance(time_cat, list):
        times = time_cat
    else:
        times = [k for k, v in sorted(time_cat.items(), key=lambda p:p[1])]
    values = payload.get("value", {})
    records = []
    for tpos, t in enumerate(times):
        coords = [0] * len(dims)
        coords[time_idx] = tpos
        linear = 0
        for coord, size in zip(coords, sizes):
            linear = linear * size + coord
        raw = values.get(str(linear)) if isinstance(values, dict) else values[linear]
        if raw is not None:
            records.append({"Period": str(t), "Value": float(raw)})
    if not records:
        raise ValueError("No available numeric observations from source")
    return pd.DataFrame(records)


def eurostat_fetch(dataset, filters):
    url = EUROSTAT + dataset
    params = {"lang":"en", "sinceTimePeriod":"2016", **filters}
    response = requests.get(url, params=params, timeout=35, headers={"User-Agent":"AcademicPortugalDashboard/1.0"})
    response.raise_for_status()
    return extract_jsonstat(response.json()), response.url


def ecb_fetch():
    response = requests.get(ECB, params={"startPeriod":"2016-01-01", "format":"csvdata"},
                            timeout=35, headers={"Accept":"text/csv"})
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
    if "TIME_PERIOD" not in df or "OBS_VALUE" not in df:
        raise ValueError("ECB response has unexpected columns")
    df = df[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"TIME_PERIOD":"Period", "OBS_VALUE":"Value"})
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df.dropna(subset=["Value"])
    if df.empty:
        raise ValueError("ECB returned no observed exchange rates")
    return df, response.url


@st.cache_data(ttl=21600, show_spinner=False)
def get_all():
    results, errors = {}, {}
    for name, spec in SERIES.items():
        try:
            df, url = eurostat_fetch(spec["dataset"], spec["filters"])
            results[name] = {**spec, "data":df, "url":url, "provider":"Eurostat"}
        except Exception as exc:
            errors[name] = str(exc)
    try:
        df, url = ecb_fetch()
        results["EUR/USD"] = {"data":df, "url":url, "provider":"European Central Bank",
                              "unit":"USD per 1 EUR", "freq":"Daily (business days)",
                              "note":"ECB reference exchange rate. Quotation: 1 euro equals X U.S. dollars; euro-area-wide, not Portugal-specific."}
    except Exception as exc:
        errors["EUR/USD"] = str(exc)
    return results, errors, datetime.now(timezone.utc).isoformat(timespec="seconds")

st.markdown("""<style>
[data-testid='stAppViewContainer'] {background: #f8f9fc;}
.block-container {padding-top:2rem;}
h1,h2,h3 {color:#173348;}
</style>""", unsafe_allow_html=True)

st.title("🇵🇹 Portugal Economic Dashboard")
st.caption("Growth • prices • employment • fiscal health • borrowing costs • currency | Official-source monitoring")

with st.sidebar:
    st.header("Dashboard controls")
    refresh = st.button("↻ Refresh source data now", use_container_width=True)
    if refresh:
        get_all.clear()
    st.info("Data are rechecked when the app is opened after the 6-hour cache expires, or when Refresh is clicked. A GitHub Actions schedule can also check the underlying sources every 6 hours.")
    st.markdown("**Primary data providers**")
    st.markdown("[Eurostat](https://ec.europa.eu/eurostat) · [ECB Data Portal](https://data.ecb.europa.eu/)")

with st.spinner("Retrieving Portugal's official economic indicators…"):
    results, errors, refreshed_at = get_all()

st.caption(f"**Last successful source-check run (UTC):** {refreshed_at} · **Latest observation date:** shown individually below (not the same as refresh time).")
if errors:
    with st.expander(f"⚠ {len(errors)} series could not load — view source diagnostics", expanded=True):
        for name, detail in errors.items():
            st.error(f"{name}: {detail}")
        st.write("Do not treat missing results as zero. Check the dataset filters using the linked Eurostat data browser.")

names = list(SERIES.keys()) + ["EUR/USD"]
for start in range(0, len(names), 3):
    cols = st.columns(3)
    for col, name in zip(cols, names[start:start+3]):
        with col:
            if name in results:
                series = results[name]
                last = series["data"].iloc[-1]
                st.metric(name, f"{last['Value']:,.2f}", help=series["unit"])
                st.caption(f"{series['unit']} · latest observation: {last['Period']}")
            else:
                st.metric(name, "Unavailable")

st.divider()
st.subheader("Historical indicators")
chosen = st.selectbox("Explore an indicator", [n for n in names if n in results]) if results else None
if chosen:
    entry = results[chosen]
    data = entry["data"].copy()
    data["Chart date"] = pd.to_datetime(data["Period"].astype(str).str.replace(r"(\d{4})-Q([1-4])", lambda m:f"{m.group(1)}-{int(m.group(2))*3-2:02d}-01", regex=True), errors="coerce")
    if data["Chart date"].notna().all():
        x = "Chart date"
    else:
        x = "Period"
    fig = px.line(data, x=x, y="Value", markers=True, labels={"Value":entry["unit"], x:"Observation period"}, template="plotly_white")
    fig.update_traces(line_color="#17638A")
    fig.update_layout(height=390, margin=dict(l=20,r=20,t=10,b=15))
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"**Definition / transformation:** {entry['note']}")
    st.write(f"**Source:** {entry['provider']} · **Frequency:** {entry['freq']} · **Units:** {entry['unit']} · **Latest observation:** {data.iloc[-1]['Period']}")
    st.markdown(f"[Open original official API result]({entry['url']})")

st.divider()
st.subheader("All indicators — source and verification table")
rows = []
for name in names:
    if name not in results:
        continue
    entry = results[name]
    last = entry["data"].iloc[-1]
    rows.append({"Indicator":name, "Latest observation":last["Period"], "Dashboard value":last["Value"],
                 "Units":entry["unit"], "Frequency":entry["freq"], "Primary source":entry["provider"], "Source URL":entry["url"]})
summary = pd.DataFrame(rows)
st.dataframe(summary, use_container_width=True, hide_index=True)
if not summary.empty:
    st.download_button("Download current verification CSV", summary.to_csv(index=False).encode("utf-8"), "portugal_verification.csv", "text/csv")
    with st.expander("Raw observations for manual source checking"):
        raw_name = st.selectbox("Choose series", list(results.keys()), key="raw_series")
        st.dataframe(results[raw_name]["data"].tail(20), hide_index=True)

st.caption("No missing data are imputed. Values are the source's published observations, not forecast figures. Different indicators have different publication lags. A refresh without new observations is still a successful retrieval.")
