# 可视化校验报告 - Phase31

**文档ID: DSHA-P31-VIS-VALIDATION** | **版本: V31.0**
**生成时间: 2029-02-02T09:00:00+08:00** | **引擎: V86.9-C-FINAL-DEBUG-P31**

---

## 校验结果: 19/19 PASS

| # | 校验项 | 结果 |
|:--:|------|:----:|
| 1 | factors_full.json结构完整 | PASS |
| 2 | backtest_AL.json字段完整 | PASS |
| 3 | backtest_PB.json字段完整 | PASS |
| 4 | backtest_CU.json字段完整 | PASS |
| 5 | backtest_ZN.json字段完整 | PASS |
| 6 | backtest_SN.json字段完整 | PASS |
| 7 | backtest_NI.json字段完整 | PASS |
| 8 | backtest_SI.json字段完整 | PASS |
| 9 | trades_AL.json交易记录完整 | PASS |
| 10 | trades_PB.json交易记录完整 | PASS |
| 11 | trades_CU.json交易记录完整 | PASS |
| 12 | trades_ZN.json交易记录完整 | PASS |
| 13 | trades_SN.json交易记录完整 | PASS |
| 14 | trades_NI.json交易记录完整 | PASS |
| 15 | trades_SI.json交易记录完整 | PASS |
| 16 | portfolio_backtest_7asset.json字段完整 | PASS |
| 17 | portfolio_daily_position.json持仓完整 | PASS |
| 18 | rolling_correlation_matrix.json多窗口完整 | PASS |
| 19 | portfolio_risk_contribution_timeseries.json时序完整 | PASS |

## 看板校验

| # | 校验项 | 结果 |
|:--:|------|:----:|
| V1 | 11个Tab面板全部渲染 | PASS |
| V2 | 概览KPI数值正确 | PASS |
| V3 | 阻断状态面板显示正确 | PASS |
| V4 | 方案D参数面板冻结状态正确 | PASS |
| V5 | 漂移趋势图数据正确 | PASS |
| V6 | 品种回测面板7品种全部显示 | PASS |
| V7 | 组合分析面板指标正确 | PASS |
| V8 | 风险贡献面板7品种完整 | PASS |
| V9 | 新品种投产面板4品种显示 | PASS |
| V10 | FR-RISK面板规则状态正确 | PASS |
| V11 | DSHC同步面板数据正确 | PASS |
| V12 | JSON数据集字段兼容DSHD相位无关CI规则 | PASS |

## 数据集字段兼容性

| 数据集 | 字段兼容性 | 说明 |
|:----:|:----------:|:----:|
| backtest_*.json | PASS | 字段名称无硬编码相位引用 |
| trades_*.json | PASS | 字段名称无硬编码相位引用 |
| portfolio_backtest_7asset.json | PASS | 字段名称兼容DSHD正则校验 |
| portfolio_daily_position.json | PASS | 字段名称兼容DSHD正则校验 |
| rolling_correlation_matrix.json | PASS | 字段名称兼容DSHD正则校验 |
| portfolio_risk_contribution_timeseries.json | PASS | 字段名称兼容DSHD正则校验 |

*校验状态: 19/19 PASS + 12/12 看板PASS = ALL PASS*
