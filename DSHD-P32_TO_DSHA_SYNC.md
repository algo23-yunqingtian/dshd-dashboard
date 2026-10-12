# DSHD-P32 to DSHA Sync - V36.0

## Status
- DSHD-P32: V36.0 DEPLOYED
- DSHA-P36: DATA DELIVERED (8/8 PASS)
- Date: 2026-10-12T05:55:33Z

## DSHA-P36 Data Confirmation
| Item | Value | Status |
|------|-------|--------|
| IC | 0.0586 | Received |
| BEAR_IC | 0.0393 | Received |
| CRISIS_IC | 0.0664 | Received |
| IR | 47.9 | Received |
| PB BEAR_IC | 0.0322 (17/17) | GRAY_ADMITTED |
| CU BEAR_IC | 0.0244 (9/14) | IMPROVING |
| Cumulative Days | 980 | Received |
| Scheme D Frozen | 11 phases | Received |
| Portfolio Vectorization | 151.4x | Received |
| Runtime | 1.151s (down 36.1%) | Received |
| Memory | 21.3MB | Received |

## P37 Data Requirements
- Date Range: 2029-10-08 ~ (estimated)
- Expected Cumulative: 1015 days
- Focus: Euler risk decomposition vectorization
- Performance: Expected 5-10% additional reduction
- Cost Model: Must integrate before live trading

## Data Format Requirements (P37)
- version_tag: P37
- dataset_version: 1.12
- All JSON files must have version_tag + dataset_version
- CI regex: ^P\d+$ and ^1\.\d+$ (phase-agnostic)
- rolling_correlation_matrix.json: must include rolling_correlation key
- portfolio_risk_contribution_timeseries.json: must include variety_time_series array

## Compatibility Status
- CI: No changes needed
- Dashboard: V36.0 fully compatible with P37 data
- All components reusable without changes
