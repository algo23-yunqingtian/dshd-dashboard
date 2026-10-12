# DSHD-P37 Version Change Report (V40.0 -> V41.0)

## Dashboard Version
- **Previous**: V40.0 (DSHD-P36)
- **Current**: V41.0 (DSHD-P37)
- **Dataset Version**: 1.15 -> 1.16 (P41)

## Metrics Changes (V40.0 -> V41.0)

| Metric | V40.0 | V41.0 | Change |
|--------|-------|-------|--------|
| CU BEAR_IC | 0.0255 | 0.0259 | +0.0004 |
| CU Gate Status | RELEASED_CONFIRMED (3/3) | RELEASED_CONFIRMED (CLOSED) | FR-RISK CLOSED |
| FR-RISK-501 Days | 1125 | 1155 | +30 |
| FR-RISK-501 Status | RELEASED_CONFIRMED | CLOSED | transitioned |
| Drift | 1.9% | 1.6% | -0.3pp |
| Cumulative Days | 1120 | 1155 | +35 |
| Frozen Phases | 15 | 16 | +1 |
| AL Stable Days | 410 | 445 | +35 |
| Float32 Max Dev | 4.700e-08 | 4.672e-08 | improved |
| T=512 boundary | - | LOCKED | mixed-precision policy |
| Incremental Speedup | 3.0x | 2.918x (3-kernel) | -2.7% |
| Euler Speedup | 110.0x | 112.6x | +2.4% |
| Runtime | 0.993s | 0.979s | -1.4% |
| NAV Gap | 3.6% | 3.6% | stable (cost model V4) |

## New/Updated Panels
1. **P40/P41 版本对比 (version-compare)** - new panel
2. **新品种 ZN/SN/NI/SI (variety-views)** - new panel (formal production)
3. FR-RISK Status Panel - CLOSED, 1155 days
4. Cost Model Panel - V4 iteration (commission 0.01% + slippage 0.6bps)
5. T=512 mixed-precision boundary LOCKED

## Cross-Agent Sync
- DSHC: P54 (DONE) | DSHA: P41 (SYNCED) | DSHD: V41.0 (DEPLOYED)
