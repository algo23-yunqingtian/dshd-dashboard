# Phase 32 Handoff - V36.0 -> P33

## Prerequisites for P33
- DSHA-P37 data delivery (Euler risk decomposition vectorization)
- Current: P36 data (PHASE36_DATA_READY.flag)

## Required Changes for V37.0
1. Update data: P36 -> P37
2. Performance panel: add P37 Euler vectorization metrics
3. CU progress bar: update 9/14 -> expected 14/14
4. New: P37 focus on risk contribution Euler decomposition vectorization

## Reusable Components
- Euler Risk Contribution Panel (renderEulerRiskContribution)
- Performance Panel (P35->P36 comparison format)
- CU Progress Bar (64.3% -> update %)
- PB dual-curve toggle (zero-cost/with-cost)
- Mobile responsive CSS (768px/480px)

## CI Compatibility
- Regex: ^P\d+$ and ^1\.\d+$ (phase-agnostic)
- No CI changes needed for P37
- version_tag: P37, dataset_version: 1.12 expected

## Key Baselines
- PB BEAR_IC: 0.0322 (17/17) | CU BEAR_IC: 0.0244 (9/14)
- IC: 0.0586 | BEAR_IC: 0.0393 | IR: 47.9
- Scheme D: FROZEN_STEADY_STATE (11 phases)
