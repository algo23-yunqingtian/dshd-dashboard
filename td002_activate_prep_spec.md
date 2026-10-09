# TD002 真实数据启用门禁规格 (TD002 Activate Prep Spec)

| Property | Value |
|----------|-------|
| Job ID | DSHD-P1-AL-CU-PB-GRAY-PHASE1-GATE-PREP |
| Document ID | PHASE1-GATE-PREP-D3 |
| Fixed Slot | 2026-10-10T09:00:00+08:00 |
| Seed | 42 |
| Mode | P2 TD 专项前置准备 (TD002 启用门禁 + TD014 解冻预配置 + V87-03/04 开发准备) |
| Dependency | PHASE1_LIVE_MONITOR_CLOSE.flag (READ-ONLY) + phase2_monitor_gate_spec.md (READ-ONLY) |
| Authority | DSHD P1 门禁准备代理 |

## 1. 定位

TD002 = AL/CU/PB 从影子/合成数据切换为**交易所真实数据**的启用门禁。本规格实例化 GATE-P2-01/02/03 的落地步骤 (真实树部署、白名单切换、3 日巡检验证), 并给出回滚与快速启用路径。真实数据到位前, 本规格为「就绪态」: 所有步骤可执行、当前状态 PENDING (数据未到, 已知状态)。

## 2. GATE-P2-01/02/03 落地 Runbook

### 2.1 GATE-P2-01 真实树部署 (探针挂载)

| 树 | 路径 (FE_WS/acd_joint_shadow_verify/dshd_sub/) | 探针 | 验收 |
|----|------|------|------|
| live x3 | v869_d_{al,cu,pb}_snapshot | 头寸校验 (position_verify_alcupb_module real) | 非空 + F39/F40 规格样本 >0 |
| ro x3 | v869_d_{al,cu,pb}_snapshot_ro_backup | RO 属性 + 版本锁 + manifest | R_OK / W_OK=False |
| delivery x3 | v869_{al,cu,pb}_release_delivery | 入站完整性 | manifest md5 一致 |

部署脚本: `phase2_gate_check_script.py` GATE-P2-01 实时判定 (当前 ABSENT -> PENDING); 数据到位后重跑即转 PASS。

### 2.2 GATE-P2-02 白名单切换

- 切换标记: 真实数据落盘并全量校验通过后, 创建 `td002_whitelist_switch.lock` (内容 `WHITELIST_SWITCHED=TRUE\nDATA_SOURCE=REAL\nFIXED_SLOT=<新槽位>\nSEED=42`)。
- 切换顺序 (快速启用路径):
  1. 真实树落盘 -> GATE-P2-01 PASS;
  2. 全量 ME01~ME06 真实树 dry-run 0 告警 -> 创建白名单锁 -> GATE-P2-02 PASS;
  3. 连续 3 日全量巡检 74/74 PASS -> GATE-P2-03 PASS;
  4. 三 PASS 齐 -> 主循环签发 GATE-P2-APPROVED。
- 回滚: 删除白名单锁 + 恢复影子树标签 (影子数据离线归档不删除, 双轨可逆)。

### 2.3 GATE-P2-03 3 日巡检验证

- 载入: phase1_live_monitor_log.csv (PATROL 轮次), 当前 2/2 轮达标, 距 3 日要求差 1 轮 (主循环每日巡检自然补齐)。
- 稳态告警定义: PATROL 轮内 FAIL=0 且告警日志无新增 CRITICAL。

## 3. TD014 SI 解冻前置配置

- 预配置文件: `td014_si_unfreeze_preconfig.json` (本工单新增, 支持文件):
  - SI 版本锁模板 (V86.9-SI-RELEASE-CANDIDATE-N 命名位);
  - RO 权限计划 (金标目录 W_OK=False + 只读完整性族保留);
  - 触发器白名单: 恢复 `ALARM-SI-*` 专项族 + ME-02/R05/R08 巡检族; 其余投产族 (K11/K12/POS/CREATE/J22/CDEV) 保持禁用直至数据达标;
  - 解除前置条件: TD014 数据扩充满足标准窗口 (FR-RISK-302 4.5 年窗补齐) + GATE-P2-08 SI 专项复核 PASS。
- 纪律: 解冻动作走**新槽位**, 旧冻结锁只读归档 (沿 V86.9-<SYM>-R2/RELEASE 锚点)。

## 4. V87-03 常驻监控服务开发准备

| 项 | 准备内容 | 状态 |
|----|----------|------|
| 调度 | v869_d_gray_patrol.py + v869_d_live_monitor.py 纳入定时调度 (日巡检 + 周快照) | 引擎已就绪, 调度壳待建 |
| 状态 | FR-RISK 接收器**持久同码计数** (进程内计数跨调用归零局限 -> daemon/state file) | 设计已定, 实现待建 |
| 告警出口 | 三色映射 + 升级链 + 停线动作标准化 (phase2_gate_check_script.py EVENT_FORMAT) | 已就绪 |

## 5. V87-04 真实头寸回放 (RISK-01/02 关闭) 开发准备

- position_verify_alcupb_module.py real 模式三品种 dry-run **3/3 PASS** (GATE-P2-07 实测) — 回放逻辑就绪。
- RISK-01/02 关闭 = 真实头寸>0 硬门取代影子全 REJECT 判据; 真实回放依赖 TD002 数据 (侧向列齐全), 同时为 FR-RISK-501 提供 bear_ratio 真实分布输入 (再校准回路, 见校准报告 §4)。

## 6. P4-2 Phase2 门禁触发事件上报格式对齐 (DSHA/DSHC)

统一事件格式 (phase2_gate_check_script.py 内置 EVENT_FORMAT):

```json
{
  "event_id": "GATE-P2-<NN>-<YYYYMMDD>-<SEQ>",
  "ts": "2026-10-10T08:00:00+08:00",
  "source": "DSHD-PHASE2-GATE",
  "gate": "GATE-P2-05",
  "item": "CHAIN_4_4",
  "status": "PASS|PENDING|FAIL",
  "severity": "INFO|WARN|CRITICAL",
  "action": "record|block",
  "evidence_refs": ["path:ch001_repair_baseline/ch001_repair_baseline_manifest.md5", "md5:..."],
  "upstream_ref": "FR-RISK-5xx | EVM-<SYM>-<YYYY>-<NN> | block-ledger-<id>"
}
```

对齐点:
- **DSHA**: 事件 `upstream_ref` 可挂 FR-RISK/EVM 编码 (v869d_ad_acl_monitor_rule.md 族); 等级映射与 A 侧风险台账严重度一致 (CRITICAL/HIGH/MEDIUM 三档)。
- **DSHC**: 块台账事件 ID (block-ledger-<id>) 回填 `upstream_ref`; 处置动作与 C 侧块台账清账事件互引。
- **D 侧**: 颜色映射 (RED=停线/ORANGE=1h/YELLOW=4h) 与 action 字段一致; 状态语义 PASS/PENDING/FAIL 跨端统一 (PENDING = 数据依赖未就位, 非缺陷)。

## 7. 风险与回滚

| 风险 | 缓解 | 回滚 |
|------|------|------|
| 真实树误挂载 (影子残留) | GATE-P2-01 非空 + 规格样本检查 | 白名单锁删除 + 影子树标签恢复 |
| 白名单切换后数据异常 | GATE-P2-03 3 日观察窗 + 稳态告警 0 | 双轨影子树离线保留, 可逆 |
| SI 解冻过早 | TD014 数据达标前置条件硬卡 | 冻结锁回写 (新槽位) |

## 8. 证据绑定

| 引用 | 路径 | MD5 |
|------|------|-----|
| 门禁脚本 | phase2_gate_check_script.py | (见 §9 复核表) |
| 门禁结果 | phase2_gate_result.csv | (见 §9) |
| 触发器族部署 | fr_risk_triggers_deploy.json | (见 §9) |
| SI 解冻预配置 | td014_si_unfreeze_preconfig.json | (见 §9) |
| 锚点/字段预留 | phase2_anchor_and_field_reserve.json | (见 §9) |
| 规格 SEALED | alcupb_contract_spec_final_manifest.md | 506a6e68d3246429c4a4cd40e6f19d9f (工单E, READ-ONLY 引用) |
