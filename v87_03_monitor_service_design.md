# V87-03 常驻监控服务设计 (V87-03 Resident Monitor Service Design)

| Property | Value |
|----------|-------|
| Job ID | DSHD-P2-AL-CU-PB-GRAY-PHASE3-GATE-RUN |
| Document ID | PHASE3-GATE-RUN-D2 |
| Fixed Slot | 2026-10-10T12:00:00+08:00 |
| Seed | 42 |
| Mode | V87 版本前置开发准备 - V87-03 常驻监控服务 |
| Dependency | PHASE2_GATE_READY.flag (fcd25d33..., READ-ONLY) + fr_risk_501_threshold_calibration_report.md (3b74c1ca..., READ-ONLY) + PHASE3_FACTOR_APPROVE.flag (b9c8c03e..., READ-ONLY) |
| Authority | DSHD P2 门禁运行 + V87 前置代理 |

## 1. 缺陷根因分析 (进程内计数归零)

- **现象**: 接收器 `v869_d_fr_risk_receiver.py` 原实现同码连续计数为**进程内 dict**, 每次 CLI 调用结束即销毁; 跨调用升级链断裂 (e.g. 501 分两次调用各 1 次, 第二次无法感知第一次的计数)。
- **根因**: 无状态接收器 (stateless CLI batch); 计数生命周期 = 进程生命周期。
- **影响**: 真实 DSHC 转发流 (常驻连续推送) 下, 同一告警码的连续窗口升级 (ORANGE x2 -> RED) 无法跨批次累计, 升级链失效。
- **工单 G 局限披露对应**: 校准报告 §5 已声明 "生产须 V87-03 常驻服务持持久计数"。

## 2. 修复方案: 持久告警计数 (已实测)

- **实现**: 接收器新增 `--persist` 模式, 升级链计数写入 `fr_risk_escalation_state.json` (跨调用载入/落盘)。
- **实测验证** (本工单, 两次独立进程调用):
  - CALL A: `--fixture persist_a --persist` -> 501 counter=1 -> **ORANGE**; state 落盘 `{"FR-RISK-501": {"count": 1, "last_event_id": "P2-501-001"}}`;
  - CALL B: `--fixture persist_b --persist` -> counter 载入 1 -> 2 -> **RED STOP_LINE (escalation)**; state 落盘 count=0 (升级后归零);
  - **跨调用升级链修复实证**: 原缺陷 (第二次调用无感知) 已消除。
- **状态文件设计**: `fr_risk_escalation_state.json` = `{counters: {<code>: {count, last_event_id}}, last_updated}`; 升级后 count=0 保留审计痕迹; 文件为运行时状态, 与审计日志分离 (日志只追加, 状态可更新)。

## 3. 常驻服务架构 (daemon)

```
                    +-----------------------+
 DSHC 转发流 ------->|  V87-03 daemon        |
                    |  - 事件接入 (转发监听)  |
                    |  - 分级映射 (mapping)  |
                    |  - 持久计数 (state)    |
                    |  - 事件持久存储 (store)|
                    |  - 告警出口 (三色)     |
                    |  - 调度器 (日巡检/周)  |
                    +----------+------------+
                               | 只追加
                  +------------v------------+
                  | 事件存储 event_store/   | 卷式轮转 (1000 条/卷)
                  | receive log + archive   | 旧卷 RO + manifest 入链
                  +-------------------------+
```

| 组件 | 设计 |
|------|------|
| 事件接入 | DSHC 转发报文 -> event_schema.json 校验 (P0-3) -> 解析 |
| 分级映射 | fr_risk_501_508_mapping.json (escalate_after/escalate_to 显式字段) |
| 持久计数 | fr_risk_escalation_state.json (本次已实测); daemon 内为内存 + 周期落盘双写 |
| 事件持久存储 | append-only 事件存储 (event_store/ + receive log); 卷式轮转 ME-04 规则沿用 |
| 告警出口 | RED=STOP_LINE / ORANGE=NOTIFY_1H / YELLOW=RECORD_4H (事件 action 字段) |
| 调度器 | 日巡检 (v869_d_gray_patrol.py 37 项) + 周期门禁 (phase2_gate_check_script.py --periodic) + 周快照 |
| 恢复 | daemon 重启载入 state + 校验 event store 连续性 (record_md5 链) |

## 4. 事件持久存储设计

- **双写**: 事件行同时写入 `fr_risk_receive_log.csv` (审计日志) + `event_store/` 卷 (全链路取证);
- **卷式轮转**: 每 1000 条开新卷; 旧卷 RO 化 + 卷清单 manifest 入链 (ME-04, 沿用);
- **取证引用**: 事件 `evidence_refs` 用统一前缀 (path:/md5:/csv:/csvline:), 与 event_schema.json 一致;
- **幂等**: record_md5 由固定槽位+事件要素派生, 重放不重复追加 (去重键 event_id)。

## 5. 与现有引擎集成

| 引擎 | 集成点 |
|------|--------|
| v869_d_gray_patrol.py | daemon 调度调用 (37 项/轮), 结果并入值守日志 |
| phase2_gate_check_script.py | --periodic 模式 (本工单已实现: 状态变更检测 + gate_periodic_check_log.csv) |
| v869_d_fr_risk_receiver.py | --persist 模式 (本工单已实现) |
| v869_d_live_monitor.py | daemon 主循环载体 (巡检+头寸+周快照) |
| position_verify_alcupb_module.py | real 回放集成 (V87-04 联动) |

## 6. 部署与测试计划

| 阶段 | 内容 | 状态 |
|------|------|------|
| 1 | 持久计数原型 (receiver --persist) | ✅ 已实现并跨调用实测 |
| 2 | 周期门禁巡检 (gate --periodic) | ✅ 已实现并 3 轮实测 (0 变更) |
| 3 | 统一事件 schema | ✅ 已落地 (event_schema.json + 示例合规) |
| 4 | daemon 壳 (调度/状态双写/事件存储) | 待主循环开发 (本设计为蓝本) |
| 5 | 真实 DSHC 转发接入 + 7 日 0 丢失验证 | 待主循环 (GATE-P2-04) |

## 7. 证据绑定

| 引用 | 路径 | MD5 |
|------|------|-----|
| 持久计数状态 (实测产物) | fr_risk_escalation_state.json | (运行时状态, 快照记录) |
| 持久验证报文 A/B | gate_prep_lab\fr_risk_persist_a_events.csv / _b_events.csv | (见复核表) |
| 接收日志 (24 行, 含 P2 轮) | fr_risk_receive_log.csv | (见复核表) |
| 统一事件 schema | event_schema.json | (见复核表) |
| 周期门禁日志 | gate_periodic_check_log.csv | (见复核表) |
| 门禁脚本 (--periodic 扩展) | phase2_gate_check_script.py | (md5 更新, 见复核表) |
| 接收器 (--persist 扩展) | v869_d_fr_risk_receiver.py | (md5 更新, 见复核表) |
