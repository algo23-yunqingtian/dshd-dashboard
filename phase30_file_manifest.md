# V34.0 File Manifest

## Summary
- **Version**: V34.0
- **Phase**: P30
- **Data Phase**: P34
- **Dataset Version**: 1.10
- **Total Files**: 175
- **Total Size**: 3,473.4 KB
- **Deployment Date**: 2026-10-12

## File Categories

| Category | Count | Description |
|----------|-------|-------------|
| HTML | 1 | index.html (main dashboard) |
| Data JSON | 47 | Core data files |
| Archive | ~127 | Historical data, reports, flags |

## Key Data Files (P34)

| File | Size | Description |
|------|------|-------------|
| factors_full.json | 7.8 KB | Factor metrics (P34) |
| backtest_AL/PB/CU/ZN/SN/NI/SI.json | ~2.7 KB each | Backtest results (P34) |
| trades_AL/PB/CU/ZN/SN/NI/SI.json | ~2.2 KB each | Trade logs (P34) |
| portfolio_backtest_7asset.json | 7.3 KB | 7-asset portfolio (P34) |
| portfolio_daily_position.json | 35.5 KB | Daily positions (P34) |
| portfolio_risk_contribution_timeseries.json | 10.3 KB | Risk contribution TS (P34) |
| rolling_correlation_matrix.json | 13.8 KB | Correlation matrix (P34, optimized) |
| version_index.json | ~X KB | Version registry (P34 ACTIVE) |
| p34_site_health.json | ~X KB | Site health (V34.0) |

## Deployment Verification
- 175/175 files uploaded via Contents API
- 2-round health check: 348/348 HTTP 200
- Latency: median 468ms, P95 505ms
- CI workflow: auto-deploy on main branch
