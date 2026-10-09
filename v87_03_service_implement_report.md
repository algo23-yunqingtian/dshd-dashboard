# V87-03 常驻监控服务实现报告 (V87-03 Service Implement Report)

| Property | Value |
|----------|-------|
| Job ID | DSHD-P3-AL-CU-PB-GRAY-PHASE4-GATE |
| Document ID | PHASE4-GATE-RUN-D1 |
| Fixed Slot | 2026-10-12T15:00:00+08:00 |
| Seed | 42 |
| Mode | V87 版本开发落地 - V87-03 常驻监控服务 daemon 实现 |
| Dependency | v87_03_monitor_service_design.md (c6d27056..., READ-ONLY) + PHASE3_GATE_RUN_READY.flag (12c22e49..., READ-ONLY) + PHASE4_FACTOR_APPROVE.flag (DSHA 侧, READ-ONLY) |
| Authority | DSHD P3 Phase4 门禁 + V87 开发代理 |

## 1. 实现交付

| 组件 | 文件 | 说明 |
|------|------|------|
| daemon 主程序 | `v87_03_monitor_service.py` | 常驻监控服务 (事件接入/映射/持久计数/事件存储/告警出口/调度器/恢复) |
| 集成测试 fixture | `gate_prep_lab/v87_03_integ_events.csv` | 跨批次升级链事件流 (501/504 x2 + 508) |
| 事件存储卷 (演练) | `gate_prep_lab/v87_03_event_store/` | vol_0001.csv + manifest.json (record_md5 链) |

## 2. 架构落地对照 (设计文档 §3)

| 设计组件 | 实现 | 实测 |
|----------|------|------|
| 事件接入 | `validate_event()` 按 event_schema.json 校验 | U1/U5 PASS (合法/非法 event_id + 证据前缀) |
| 分级映射 | `map_event()` 按 fr_risk_501_508_mapping.json (escalate_after/escalate_to) | U2/U4 PASS (501->ORANGE, 502 立即 STOP_LINE) |
| 持久计数 | `load_state/save_state` 双写 (内存 dict + fr_risk_escalation_state.json) | 集成测试跨批延续 501/504 -> RED STOP_LINE |
| 事件持久存储 | `store_events()` append-only 卷式轮转 (VOL_LIMIT=1000) + manifest | 5 事件落卷, record_md5 链连续性校验 OK |
| 告警出口 | action 字段 RED=STOP_LINE / ORANGE=NOTIFY_1H / YELLOW=RECORD_4H | U3/U4 断言 |
| 调度器 | `--mode patrol` 调用 gray_patrol 37 项 (计时) | 37 项 0.09s PASS (<60s J14) |
| 恢复 | `recover()` 载入 state + 校验 event store record_md5 链 | 集成测试后 recover ok=True, chain=OK |

## 3. 测试结果

### 3.1 单元测试 (selftest)

| # | 用例 | 结果 | 断言 |
|---|------|------|------|
| U1 | SCHEMA | PASS | 合法/非法 event_id 校验正确 |
| U2 | 501-ORANGE | PASS | 首击 HIGH/ORANGE count=1 |
| U3 | ESC-RED | PASS | 同码连续 2 次 -> CRITICAL/RED STOP_LINE, 计数归零 |
| U4 | 502-STOP | PASS | 立即 STOP_LINE (无升级计数) |
| U5 | EVIDENCE-PREFIX | PASS | http: 非法前缀被拒 |
| U6 | VOL-LIMIT | PASS | VOL_LIMIT=1000 |

**6/6 PASS** (slot=2026-10-12T15:00:00+08:00)

### 3.2 集成测试 (integtest)

- 输入: 5 事件 (batch A: 501/504 首击; batch B: 501/504 延续 + 508 立即);
- 批间通过 `fr_risk_escalation_state.json` 落盘/载入模拟 daemon 重启;
- 结果: **stored=5, recover_ok=True, chain=OK, tail_ok=True**;
- 升级链: 501/504 跨批次延续 -> 2 次 -> **RED STOP_LINE** (进程内计数归零缺陷修复实证);
- 508 立即 CRITICAL, 计数 1 无升级 (符合 mapping 无 escalate 字段语义);
- state 终态: {"FR-RISK-501": 0, "FR-RISK-504": 0, "FR-RISK-508": 1} (升级后归零保留审计痕迹).

### 3.3 调度器 (patrol)

- 37 项全 PASS, 耗时 0.09s (<60s J14 线);
- 复用 v869_d_gray_patrol.py 零改动 (import 调用).

### 3.4 恢复 (recover)

- 载入 manifest + 逐行重算 record_md5 链, 与 manifest tail_md5 比对;
- 结果: vols=1 rows=5 chain=OK tail_ok=True.

## 4. 事件 schema 对齐 (P0-3 联动)

- 本工单发现并修正 schema 内部不一致: event_id 描述段无日期, 与 pattern `-[0-9]{8}-` 冲突;
- 修正为 `FR-RISK-<NNN>-<SYM>-<YYYYMMDD>-<SEQ>` (REV1, 与 pattern 自洽);
- GATE PENDING 事件 severity 规范为 INFO (RECORD), FAIL 为 CRITICAL (BLOCK), 避免 enum 外值;
- 修正后验证: FR-RISK 3/3 + GATE 11/11 schema 合规.

## 5. 生产部署差异与移交

| 项 | 演练态 (本工单) | 生产态 (移交主循环) |
|----|----------------|--------------------|
| 事件源 | lab fixture CSV | 真实 DSHC 转发通道 (GATE-P2-04 7 日 0 丢失验证) |
| 事件存储 | gate_prep_lab/v87_03_event_store/ | OUT_DIR/event_store/ 卷式轮转 (1000/卷, 旧卷 RO + manifest 入链) |
| 调度 | 手动 --mode | 常驻循环 (周期巡检 + 日巡检 + 周快照) |
| 持久计数 | 状态文件已就位 | 已就位 (本工单实测跨调用延续) |

## 6. 证据绑定

| 引用 | 路径 | MD5 |
|------|------|-----|
| daemon 主程序 | v87_03_monitor_service.py | (见复核表) |
| 集成 fixture | gate_prep_lab/v87_03_integ_events.csv | (见复核表) |
| 事件存储卷 | gate_prep_lab/v87_03_event_store/ | (运行时演练产物) |
| 设计蓝本 (只读) | v87_03_monitor_service_design.md | c6d27056d86e2a85ff878def8d982090 |
| 统一 schema (REV1) | event_schema.json | (见复核表, 本工单修正) |
| 周期门禁 | gate_periodic_check_log.csv | (见复核表, PG4-R1~R3) |
