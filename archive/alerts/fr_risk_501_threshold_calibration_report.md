# FR-RISK-501 bear_ratio 阈值校准报告

| Property | Value |
|----------|-------|
| Job ID | DSHD-P1-AL-CU-PB-GRAY-PHASE1-GATE-PREP |
| Document ID | PHASE1-GATE-PREP-D2 |
| Fixed Slot | 2026-10-10T08:30:00+08:00 (校准) / 08:45:00 (e2e) |
| Seed | 42 |
| Mode | FR-RISK 专项校准 - 501 bear_ratio 阈值 + 502~508 映射确认 |
| Dependency | PHASE1_LIVE_MONITOR_CLOSE.flag (0f6cd47e..., READ-ONLY) + phase2_monitor_gate_spec.md (88803c9d..., READ-ONLY) |
| Authority | DSHD P1 门禁准备 + FR-RISK 校准代理 |

## 1. 校准目标与输入数据

- 目标: 对 FR-RISK-501 (CU BEAR 区持仓风险) 的 bear_ratio 阈值 0.60 做校准, 输出可执行阈值与再校准回路。
- bear_ratio 定义: `bear_ratio = 空头(BEAR/SELL/SHORT)记录数 / 总头寸记录数` (方向列 side 缺失的记录不参与)。
- 输入: Phase1 影子回测/值守样本 (gate_prep_lab 头寸日志), 实测如下:

| 样本 | 来源 | 方向列 | bear_ratio | 判定 |
|------|------|--------|-----------|------|
| AL_gray_ok | al_gray_ok_position_log.csv (pos 2/0) | 无 | 无信号 (0 空头记录) | NORMAL |
| CU_gray_ok | cu_gray_ok_position_log.csv (pos 2/0) | 无 | 无信号 | NORMAL |
| PB_gray_ok | pb_gray_ok_position_log.csv (pos 1/0) | 无 | 无信号 | NORMAL |
| CU_BEAR_INJECTED | cu_bear_position_log.csv (BEAR x3 / BILL x1) | BEAR/BILL | **0.75** (3/4) | RISK (注入) |
| CU_REJECT | cu_reject_position_log.csv (全 REJECT) | 无 | n/a (offline 全拒) | 不参与 |

## 2. 方法: 敏感性分析

对可用样本 (4 个: 3 NORMAL 无空头信号 + 1 RISK 0.75), 扫描阈值 T 评估误报 (FP) / 漏报 (FN):

| T | 0.40 | 0.45 | 0.50 | 0.55 | **0.60** | 0.65 | 0.70 | 0.75 | 0.80 |
|---|------|------|------|------|---------|------|------|------|------|
| FP | 0 | 0 | 0 | 0 | **0** | 0 | 0 | 0 | 0 |
| FN | 0 | 0 | 0 | 0 | **0** | 0 | 0 | 1 | 1 |

- 安全带: **T ∈ [0.40, 0.70] 零 FP / 零 FN** (对现有影子数据)。
- 边界: T ≥ 0.75 将漏检注入风险样本 (0.75 不 > 0.75) -> 阈值必须 < 0.75。
- 正常运营样本均无空头方向记录 -> bear_ratio=0 与风险样本 0.75 分离间隙 = 0.75, 阈值 0.60 位于间隙上半 (保守偏右, 倾向少告警, 由 1h SLA + 升级链兜底)。

## 3. 校准结论

**FR-RISK-501 bear_ratio 阈值维持 0.60 (校准通过, 确认有效)**

- 触发验证: 注入样本 0.75 > 0.60 -> ORANGE (实测 FWD-501-001); 窗口内第 2 次 -> RED STOP_LINE (实测 FWD-501-004)。
- 建议运行带: **0.55 ~ 0.65** (维持 0.60 主阈值; 参数化便于真实数据再校准)。
- 增强判定 (预留): `bear_ratio > T OR 净空名义占比 > 0.60` (加权口径, 需方向列齐全的真实头寸回放, V87-04)。

## 4. 真实数据再校准回路 (TD002 启用后, 主循环)

1. TD002 真实数据就位 + V87-04 真实头寸回放 (RISK-01/02 关闭) 后, 采集 **20 个真实交易日** CU 头寸方向分布;
2. 计算正常运营 bear_ratio 分布 -> 建议阈值 = max(0.60, p90(normal) + 0.10 裕度);
3. 阈值变更经新槽位回写 (fr_risk_501_508_mapping.json / fr_risk_triggers_deploy.json), 历史阈值 0.60 归档只读。

## 5. 502~508 映射确认与全链路端到端测试 (P1-2)

- 部署: fr_risk_triggers_deploy.json (8 触发器 ACTIVE, escalate_after/escalate_to 与 mapping 完全一致)。
- e2e: gate_prep_lab/fr_risk_e2e_events.csv 13 事件全链实测, **13/13 与预期零失配**:

| 码 | 链 | 实测序列 | 三端对齐 (语义/等级/处置) |
|----|----|----------|---------------------------|
| 501 | 3 连 | ORANGE -> RED(STOP_LINE) -> ORANGE (计数归零复位) | CU BEAR 集中 / HIGH->CRITICAL / NOTIFY_1H->STOP_LINE |
| 504 | 2 连 | ORANGE -> RED | K12 偏离 / HIGH->CRITICAL / NOTIFY_1H->STOP_LINE |
| 505 | 3 连 | YELLOW -> YELLOW -> ORANGE | J22 跨端 / MEDIUM->HIGH / RECORD_4H->NOTIFY_1H |
| 502/503 | 单发 | RED STOP_LINE x2 | 头寸硬门/K11 / CRITICAL / STOP_LINE |
| 506 | 单发 | YELLOW | 轮转失败 / MEDIUM / RECORD_4H |
| 507 | 单发 | ORANGE | 冻结只读 / HIGH / NOTIFY_1H |
| 508 | 单发 | RED | CHAIN 缺失 / CRITICAL / NOTIFY_2H |

- 升级链稳定性: 501 三连验证「升级后计数归零」; 504/505 验证 escalate_after 2/3 精确触发。
- 接收器局限 (诚实披露): 同码连续计数为**进程内状态**, 跨调用归零; 生产真实转发需 V87-03 常驻服务持持久计数 (state file / daemon), 已列入移交项。

## 6. 证据绑定

| 引用 | 路径 | MD5 |
|------|------|-----|
| 触发器族部署 | fr_risk_triggers_deploy.json | (见 §7 复核表) |
| e2e 报文 | gate_prep_lab\fr_risk_e2e_events.csv | (见 §7) |
| 接收日志 (22 行) | fr_risk_receive_log.csv | (见 §7) |
| 501 注入样本 | gate_prep_lab\cu_bear_position_log.csv | 36d02c7a9923f0abb6972db2618f2b56 |
| 501 快照样本 | gate_prep_lab\cu_bear_snapshot.csv | 51dd8601796dc8bce3bc6ad35873ead9 |
| 映射配置 (0.60 基准) | fr_risk_501_508_mapping.json | 41efa5a041de70446a0732665a4d42f6 (工单F, READ-ONLY 引用) |
