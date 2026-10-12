# DSHD-P35 Cost Model Integration Notes

## Overview
P39 introduces the cost model integration panel, showing the gap between
zero-cost and cost-adjusted backtest results.

## Key Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| NAV (zero-cost) | 1.884 | Baseline |
| NAV (cost-adjusted) | 1.817 | Commission + slippage |
| NAV Gap | 3.6% | Stable across phases |
| Annual Return Overestimate | 6.7pp | Zero-cost model bias |
| Total Cost Rate | 0.22% | Commission 0.02% + Slippage 2bps |
| Audit Severity | MEDIUM (YELLOW) | Requires live integration |

## Cost Breakdown
- Commission: 0.02% (per side)
- Slippage: 2 bps (20 bps round-trip)
- Total round-trip cost: 0.22%

## Integration Status
- [x] Dual-version backtest (zero-cost + cost-adjusted)
- [x] Cost-adjusted NAV calculation
- [x] Cost breakdown display
- [ ] Live trading cost integration
- [ ] Annual return correction

## Recommendation
Integrate cost model before live trading. Current zero-cost model overestimates
annual return by 6.7 percentage points. The cost-adjusted NAV (1.817) provides
a more realistic performance estimate.
