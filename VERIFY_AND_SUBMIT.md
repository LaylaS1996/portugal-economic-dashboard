# Portugal dashboard: verification and submission checklist

## Evidence to capture
- [ ] Screenshot of deployed Streamlit dashboard showing indicator cards and last successful refresh.
- [ ] Screenshot of one or two historical indicator charts showing source labels/observation dates.
- [ ] Click Refresh; take a screenshot of the refreshed timestamp. Note that unchanged data can still count as a successful refresh.
- [ ] Export current verification CSV.
- [ ] Compare a GDP observation and an inflation observation against original Eurostat data and note the exact observation period and value.
- [ ] If using GitHub Actions, save a screenshot of a successful scheduled 'Refresh source check' run.

## Manual verification log (fill in from live data)
| Indicator | Observation period | Dashboard value | Original-source value | Match? | Checked at (UTC) |
|---|---|---|---|---|---|
| Real GDP growth | | | | | |
| Inflation (HICP) | | | | | |

## Submission
1. Dashboard URL and screenshot
2. AI_PROMPT.txt
3. Verification log / CSV and successful-refresh screenshot or GitHub Actions log

## Important
No live indicator figures were pre-populated in this package. The app must successfully connect to the official APIs to produce and verify real values.
