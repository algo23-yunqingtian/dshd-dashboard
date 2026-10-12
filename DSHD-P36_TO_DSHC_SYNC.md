# DSHD-P36 → DSHC SYNC

| Field | Value |
|-------|-------|
| From | DSHD-P36 (V40.0 dashboard) |
| To | DSHC (P51) |
| Timestamp | 2026-12-13T18:00:00+08:00 |
| Status | SYNCED |

## Deployed Dashboard
- URL: https://algo23-yunqingtian.github.io/dshd-dashboard/
- Version: V40.0 | Dataset 1.15 | Engine V86.9-C-FINAL-DEBUG-P40
- Tabs: 18 | Panels: 17 (FR-RISK, Rolling-F32, Cost-Model + 14 legacy)

## Metrics Delivered to DSHC
| Metric | Value | Change vs P39 |
|--------|-------|---------------|
| CU BEAR_IC | 0.0255 | +0.0002 (3/3 confirmed) |
| PB BEAR_IC | 0.0322 | 0 (20/20 sustained) |
| FR-RISK-501 | 1125 days | +35 (RELEASED_CONFIRMED) |
| Drift | 1.9% | -0.1pp (15 phases <4.8%) |
| Cumulative | 1120 days | +35 |
| Frozen phases | 15 | +1 |
| AL stable | 410 days | +35 |
| Float32 gate | PASS 4.700e-08 | stable |
| Incremental | 3.0x | +0.055x |
| Euler | 110.0x | +1.8x |
| Runtime | 0.993s | +0.002s |
| NAV gap | 3.6% | stable |

## AC Status: 8/8 PASS
- AC1: Scheme D frozen (P28+, 15 phases)
- AC2: Float32 dual-branch max_dev 4.700e-08 <= 1e-6
- AC3: 7-variety parallel backtest, dual NAV, gap 3.6%
- AC4: CU 3 consecutive phases >= 0.025 gate
- AC5: DSHD V40.0 structured JSON, validation 86/86 PASS
- AC6: Docs archived (archive/P36/), weekly W42
- AC7: SHA256 verified, baseline chain intact
- AC8: PHASE40_DATA_READY.flag + PHASE36_DONE.flag issued

## Next
- DSHD-P37 V41.0 (await DSHA-P41)
- DSHC-P52 (pending execution)
