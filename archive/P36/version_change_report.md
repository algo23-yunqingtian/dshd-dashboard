# DSHD-P36 Version Change Report (V39.0 -> V40.0)

## Dashboard Version
- **Previous**: V39.0 (DSHD-P35)
- **Current**: V40.0 (DSHD-P36)
- **Dataset Version**: 1.14 -> 1.15

## Metrics Changes (V39.0 -> V40.0)

| Metric | V39.0 | V40.0 | Change |
|--------|-------|-------|--------|
| CU BEAR_IC | 0.0253 | 0.0255 | +0.0002 |
| CU Gate Status | RELEASED_CONFIRMED (2/2) | RELEASED_CONFIRMED (3/3) | +1 confirmation |
| FR-RISK-501 Days | 1090 | 1125 | +35 |
| Drift | 2.0% | 1.9% | -0.1pp |
| Cumulative Days | 1085 | 1120 | +35 |
| Frozen Phases | 14 | 15 | +1 |
| AL Stable Days | 375 | 410 | +35 |
| Float32 Max Dev | 4.672e-08 | 4.700e-08 | +2.8e-11 |
| Incremental Speedup | 2.945x | 3.0x | +0.055x |
| Euler Speedup | 108.2x | 110.0x | +1.8x |
| Runtime | 0.991s | 0.993s | +0.002s |
| NAV Gap | 3.6% | 3.6% | 0.0% |

## New/Updated Panels
1. **FR-RISK Status Panel** - 1125 days, 3/3 confirmations, RELEASED_CONFIRMED
2. **Rolling Correlation F32 Panel** - P40 monitoring, AUTO_FALLBACK maintained
3. **Cost Model Panel** - NAV gap 3.6% stable, annual overestimation 6.7pp

## Files Changed
- index.html (V39.0 -> V40.0)
- 45 JSON files (dataset_version 1.14 -> 1.15)
- PHASE40_DATA_READY.flag, PHASE36_DONE.flag, p40_site_health.json, cost_model_integration.json

## Cross-Agent Sync
- DSHC: P51 (SYNCED) | DSHA: P40 (SYNCED) | DSHD: V40.0 (DEPLOYED)
