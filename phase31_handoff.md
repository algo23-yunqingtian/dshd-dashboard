# DSHD-P31 Handoff → P32

## Current Status

| Item | Value |
|------|-------|
| Dashboard | V35.0 |
| Data Phase | P35 |
| Cumulative Days | 945 |
| Live URL | https://algo23-yunqingtian.github.io/dshd-dashboard/ |

## Prerequisites for P32

- DSHA-P36 data delivery (PHASE36_DATA_READY.flag)
- Expected cumulative: 980 days
- Expected date: 2029-08-19

## Required Changes (P32)

1. **Data Layer**: Update all 47 JSON files P35→P36
2. **HTML**: V35.0→V36.0
   - Version badges, titles, headers
   - Panel headers (FR-RISK, PB/CU, correlation, IC drift)
   - Footer, state config, JS references
3. **Performance Panel**: Update metrics (portfolio vectorization evaluation)
4. **CU Progress**: Track 9/14 → 14/14 target
5. **Gray Admission**: Update PB/CU BEAR_IC values

## Reusable Components

- PB dual-curve toggle (togglePBNav, computeWithCostNAV, renderPBNavDualChart)
- Null safety helpers (safeVal, safeText, safePct, safeStatus, safeNav)
- Performance panel template
- CU progress bar component
- Mobile responsive CSS
- Fetch error handling wrapper

## CI Notes

- CI regex is phase-agnostic (^P\d+$, ^1\.\d+$)
- No CI changes needed for P36
- rolling_correlation_matrix.json needs rolling_correlation key (P35 fix)
- portfolio_risk_contribution_timeseries.json needs variety_time_series (P35 fix)

## Key Files

| File | Path |
|------|------|
| HTML | web_site/index.html |
| Data | web_site/data/*.json |
| Archive | web_site/archive/ |
| CI | .github/workflows/deploy-pages.yml |
