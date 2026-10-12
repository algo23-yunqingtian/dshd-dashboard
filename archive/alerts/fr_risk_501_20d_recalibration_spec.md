# FR-RISK-501 20 日窗二次阈值校准流程 (20-Day Recalibration Spec)

| Property | Value |
|----------|-------|
| Job ID | DSHD-P2-AL-CU-PB-GRAY-PHASE3-GATE-RUN |
| Document ID | PHASE3-GATE-RUN-D5 |
| Fixed Slot | 2026-10-10T12:45:00+08:00 |
| Seed | 42 |
| Mode | FR-RISK 专项 - 501 真实数据二次阈值校准流程预留 (V87-04 联动) |
| Dependency | fr_risk_501_threshold_calibration_report.md (3b74c1ca..., READ-ONLY) + v87_04_playback_prep_checklist.md (本工单 D3) |
| Authority | DSHD P2 门禁运行 + FR-RISK 校准代理 |

## 1. 目的

TD002 真实数据 + V87-04 真实头寸回放就绪后, 用 **20 个真实交易日** CU 头寸方向分布对 FR-RISK-501 bear_ratio 阈值 (现 0.60) 做二次校准, 消除影子数据样本稀薄局限, 输出真实运营阈值。

## 2. 前置条件 (全绿才启动)

| 条件 | 判定 |
|------|------|
| TD002 白名单切换 | td002_whitelist_switch.lock 存在 (GATE-P2-02 PASS) |
| 真实头寸回放 | V87-04-R1..R6 全 PASS (真实树 + real 硬门 + side 列齐全) |
| 20 日窗数据 | 连续 20 个真实交易日头寸方向分布, 无缺口 (缺日顺延) |

## 3. 统计方法

1. 每日计算 `bear_ratio_d = 空头记录数 / 总记录数` (side 列 BEAR/SHORT/SELL 分类, 口径同校准报告 §1);
2. 20 日分布 -> 正常运营 bear_ratio 集合 B = {b1..b20};
3. 建议阈值 `T_new = max(0.60, p90(B) + 0.10)` (保留保守下限, 叠加裕度);
4. 敏感性复核: 对 B 重算 FP/FN (参照 0.60 安全带 [0.40,0.70] 方法), 输出 T_new 的 FP/FN=0 实证。

## 4. 阈值决策规则

| 情形 | 决策 |
|------|------|
| p90(B)+0.10 <= 0.60 | 维持 0.60 (影子校准保守值仍成立) |
| p90(B)+0.10 > 0.60 且 T_new <= 0.75 | 采纳 T_new (须 < 0.75 漏检边界) |
| T_new >= 0.75 | 不采纳, 维持 0.60 并复盘 (0.75 会漏检注入样本, 见校准报告 §2) |

## 5. 回写流程 (新槽位纪律)

1. 校准结论 -> 新槽位记录 (本流程附录追加版本, 历史不改写);
2. 回写 `fr_risk_501_508_mapping.json` (mapping 501 trigger) + `fr_risk_triggers_deploy.json` (TRG-FRRISK-501 阈值字段);
3. 阈值变更登记基线变更事件 (变更前后值 + 依据 20 日窗数据);
4. 旧阈值 0.60 归档只读。

## 6. 验证与回滚

| 项 | 内容 |
|----|------|
| 验证 | T_new 生效后 7 日观察: 正常运营 FP=0, 注入/真实风险触发 ORANGE/RED 正常 |
| 回滚 | 新槽位回写旧阈值 0.60 (归档记录恢复), 观察窗数据保留 |

## 7. 证据绑定

| 引用 | 路径 | MD5 |
|------|------|-----|
| 校准报告 (0.60 基线) | fr_risk_501_threshold_calibration_report.md | 3b74c1cad5794cf3bae5aaebdbc56c74 (工单G, READ-ONLY) |
| 回放清单 (R7 联动) | v87_04_playback_prep_checklist.md | (本工单 D3) |
| 映射配置 (回写对象) | fr_risk_501_508_mapping.json | 41efa5a041de70446a0732665a4d42f6 (工单F, READ-ONLY 当前) |
| 触发器部署 (回写对象) | fr_risk_triggers_deploy.json | (工单G, READ-ONLY 当前) |
| 501 注入样本 | gate_prep_lab\cu_bear_position_log.csv | 36d02c7a9923f0abb6972db2618f2b56 |
