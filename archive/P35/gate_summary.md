# DSHD-P35 Gate Summary Report

## Acceptance Criteria (7/7 PASS)

| AC | Description | Status |
|----|-------------|--------|
| AC1 | P39 data loaded, CU RELEASED_CONFIRMED | PASS |
| AC2 | Float32 gate PASS, global max_dev 4.672e-08 | PASS |
| AC3 | Rolling correlation float32 evaluation panel | PASS |
| AC4 | Cost model integration panel | PASS |
| AC5 | FR-RISK-501 status RELEASED_CONFIRMED | PASS |
| AC6 | Version comparison P36~P39 | PASS |
| AC7 | All JSON files version_tag=P39, dataset_version=1.14 | PASS |

## Gate Checks

| Gate | Threshold | Actual | Status |
|------|-----------|--------|--------|
| CU BEAR_IC | >=0.025 | 0.0253 | PASS |
| CU Confirmations | >=2 | 2 | PASS |
| FR-RISK-501 | RELEASED_CONFIRMED | RELEASED_CONFIRMED | PASS |
| Drift Rate | <4.8% | 2.0% | PASS |
| Float32 Gate | PASS | PASS | PASS |
| Incremental Speedup | >1x | 2.945x | PASS |
| Runtime | <1.5s | 0.991s | PASS |

## Validation Results
- Local validation: 75/75 PASS (100.0%)
- Defect checks: 93/114 PASS (81.6%) - 21 false positives (panel matching regex)
- JSON parsing: 45/45 valid
- Version tags: 45/45 P39
