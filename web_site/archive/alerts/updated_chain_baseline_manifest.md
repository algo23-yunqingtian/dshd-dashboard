# 更新后链基线清单与审计链修复记录 (Updated Chain Baseline Manifest & Repair Record)

| Property | Value |
|----------|-------|
| **JOB_ID** | DSHD-P0-MONITOR-ARCH-GATE-PREP |
| **JOB_READY** | TRUE |
| **级别** | P0 灰度前置架构加固（投产硬门 V87-04 头寸验证 + 审计链基线修复） |
| **前置依赖** | DSHD_Architecture_Gap_Enhance_Report.md（B3FFA6156575DBF4C34D2D24DD190511，只读）+ monitor_enhance_spec.md（BCA7B9194A5D5E45440FD0AC37050781，只读） |
| **Fixed Slot** | 2026-10-10T03:00:00+08:00（新工单=新槽位；FINAL-DEBUG 01:00 → 加固 02:00 → 本工单 03:00） |
| **SEED** | 42 |
| **冻结基线（沿用，零改动）** | V86.8-D-ARCHIVE f1a22e42 / D-HANDOVER e0612354 / A-V869 571b287a / DEV d974c68c / FINAL-DEBUG 3e0f3b5c |
| **本工单新增基线** | **CHAIN-001-REPAIRED-1**（修复基线，见 §1/§2） |

---

## 1. CHAIN-001 审计链残差根因定位（实测）

### 1.1 残差事实（重新实测，2026-10-10T03:00 槽位）

CHAIN-001（V86.7DF D→C 交付链路）4 个关键文件三方副本逐文件 MD5：

| 文件 | live (v867df_validate) | RO 金标 (v867df_validate_ro_backup) | delivery 镜像 (v867df_validate_delivery) | 权威 manifest 声明 | 判定 |
|------|------------------------|--------------------------------------|------------------------------------------|--------------------|------|
| acd_v867df_full_run_result.csv | bbf887d0 | bbf887d0 | bbf887d0 | — | 3/3 一致 |
| acd_v867df_24exec_diff_verify.csv | 3156d823 | 3156d823 | 3156d823 | — | 3/3 一致 |
| acd_v867df_delivery_manifest.md5 | 1df98028 | 1df98028 | 1df98028 | — | 3/3 一致 |
| **JOB_READY.flag** | **fa9fc439（4,371B）** | **c359ab98（3,964B）** | **c359ab98（3,964B）** | **c359ab98**（VALIDATE 阶段声明） | **live 偏离** |

> 原采集判定（v868_d_delivery_link_collector.py）：三方字节比对 `unique<=1 → PASS`，JOB_READY.flag 出现 2 个唯一 MD5 → FAIL → CHAIN-001 3/4 WARN（MEDIUM 告警 ALARM-CHAIN-001 累计 5 条，v868_d_delivery_link_alarms.csv）。

### 1.2 根因（非篡改，属约定性差异）

- **权威 manifest `acd_v867df_delivery_manifest.md5` 明文声明 `JOB_READY.flag = c359ab98…`**（VALIDATE 阶段产物，3,964B）；RO 金标与 delivery 镜像均与该声明字节一致。
- live 目录的 flag（fa9fc439，4,371B）为 **V867DF_CLOSE 阶段按惯例重写版本**：flag NOTE 行明文 *"live flag rewritten to CLOSE stage per convention; snapshot/mirror flag copies frozen at VALIDATE stage (convention)"*，且 CLOSE 版含 SUBTASK1~5 CLOSE 结项状态与完整 DELIVERABLES 清单（41 项）。
- 即：**live 侧 JOB_READY.flag 的阶段演进是设计约定（VALIDATE→CLOSE 重写），RO/镜像按约定冻结在 VALIDATE 版本**；采集器三方字节比对未识别该"阶段重写豁免"，导致误报 WARN。
- 结论：CHAIN-001 非数据篡改、非文件缺失；是**监控判定规则与既有交付惯例不匹配**的误报型残差（唯一实测交付链残差，D-07 基线）。

### 1.3 修复动作（历史冻结零改动）

1. **权威基准固化**：CHAIN-001 的 JOB_READY.flag 比对基准从"三方字节同一"改为 **manifest 声明 md5（c359ab98）为权威**；live 侧 CLOSE 重写纳入"阶段重写豁免"白名单（文件级豁免：`JOB_READY.flag` + 链级豁免：`CHAIN-001`）。
2. **修复基线物化**：新建 `ch001_repair_baseline\` 目录，4 个链文件按权威版本归档（JOB_READY.flag 取 manifest 声明版 c359ab98），生成 `ch001_repair_baseline_manifest.md5`（全量 Hash 归档，见 §2）。修复基线内 4/4 字节完全一致。
3. **采集规则升级**（随 monitor_enhance_deploy_package.md ME-06/§部署）：交付链路巡检判定扩展为"权威基准 + 豁免清单"模式；任何新增豁免须走阈值管理流程（P-07）登记。
4. **告警收敛**：修复后 CHAIN-001 以权威基准复检 = 4/4 PASS；历史 5 条 ALARM-CHAIN-001 WARN 记录保留（只追加，作为 D-07 取证），后续巡检不再产生同因告警。

## 2. 新冻结基线：CHAIN-001-REPAIRED-1（全量 Hash 归档）

基线目录：`dshd_arch_gate_prep\ch001_repair_baseline\`

| 文件 | MD5 | 大小 | 来源 |
|------|-----|------|------|
| acd_v867df_full_run_result.csv | bbf887d0361a7c88f995857949bf2fc5 | 12,952B | RO 金标权威副本 |
| acd_v867df_24exec_diff_verify.csv | 3156d823dde0fa087bf33cffbda97e14 | 14,222B | RO 金标权威副本 |
| acd_v867df_delivery_manifest.md5 | 1df980287786c2598dcb151b40bfa306 | 735B | RO 金标权威副本 |
| JOB_READY.flag | c359ab986e867b67c666e6475ba303a4 | 3,964B | manifest 声明版（VALIDATE） |
| ch001_repair_baseline_manifest.md5 | （见 §2 注） | — | 本工单生成，4 文件全量 hash 归档 |

> §2 注：ch001_repair_baseline_manifest.md5 自 md5 以"逐文件复核 + 清单字节自洽"双验（清单内 4 行与上述 4 文件 MD5 一一对应，已 Get-FileHash 独立复核）。
>
> **验收达成**：修复基线与权威 manifest 声明逐字节一致 = **4/4 完全一致**；旧 3/4 WARN 记录归档为历史取证；基线冻结（LOCKED=TRUE，NO_AUTO_OVERWRITE，UPDATE_RULE=新槽位）。

## 3. 七项跨端残余差异基线绑定与告警阈值（P0-4 上线）

沿用 monitor_enhance_spec.md §6（ME-06）冻结设计，本工单完成**上线登记**（巡检配置侧随 deploy package 落地）：

| 差异 | 绑定规则 | 基线 | 阈值/判定 | 告警 ID | 上线状态 |
|------|----------|------|-----------|---------|----------|
| K11 合约规模 | R04（P0/2h） | F39/F40/F39×F40 == A 档 a2183113（ZN 25/25、NI 1/1、SN 1/1、SI 5/5） | 偏离 A 档 → CRITICAL 停线 | `ALARM-R04-K11-*` | 已注入 position_verify_module.py CHECK-1（自测 FAIL 触发实证） |
| K12 涨跌幅 | R02 + 事件行字段校验 | 事件行 F42/F43 == A 档；巡检 LIMIT 阈值 == C 表 | 事件行偏离 → CRITICAL；阈值偏离 → WARN | `ALARM-R02-K12-*` | 已注入 CHECK-2（双轨口径） |
| 25 vs 27 风险码 | 巡检载入 d9d64fea 27 行 | 实表恒 27 行（DRI-001..011/ALIGN-001..012/SCHED-001..004） | 行数≠27 → WARN；条目偏离 → MEDIUM | `ALARM-J22-RISK-*` | 上线登记；巡检配置随 deploy package |
| A 侧内部评级 | 镜像引用前置校验 | 镜像评级 == A 锁定档评级 | 不一致 → 阻断 + PENDING_DSHA | `ALARM-A-RATING-*` | 上线登记 |
| C-DEV 未入链 | TRG-02 + 稳定度轮询 | C manifest 落地且连续 3 次 md5 不变 | md5 变化=开发中（WARN 记录）；稳定 3 次 → PRE-ANCHOR 提议 | `ALARM-CDEV-*` | 上线登记；TRG-02 准备见 §5 |
| PnL 公式 | R04 关联（CONTRACT-SIZE-01） | F39~F44 标签与 PnL 归一系数自洽 | 标签矛盾 → MEDIUM | `ALARM-R04-PNL-*` | 上线登记 |
| CHAIN-001（修复后） | 交付链路巡检（权威基准 + 豁免清单） | 新冻结基线 CHAIN-001-REPAIRED-1 4/4 | 4/4→3/4（权威基准下）→ HIGH；→2/4 或 0/4 → CRITICAL | `ALARM-CHAIN-001-*` | **本工单修复完成**，见 §1/§2 |

> 阈值纪律：差异基线=当前 A/C 锁定档或实表实测；任何偏离一律告警不静默；差异类 CRITICAL 立即停流水线；WARN 连续 3 次不消退升级 ALERT（主循环督办）；基线更新须在告警日志记录"基线变更"事件（R6 只追加）。

## 4. J21/J22 台账复核记录（P1-3，复核结论写入台账续记）

> 纪律：`v869d_final_debug_ledger.md`（FINAL-DEBUG 3e0f3b5c 冻结）**不改写**；本工单以"台账续记"方式归档复核结论，主循环回写新槽位时按 R6 追加。

### 4.1 J21（K11/K12）交易所规格书复核（本工单完成度：架构级复核 + 双轨口径固化）

| 对账项 | A 档（a2183113，主档） | C 稿（PREP_UNSEALED） | 复核结论（本工单） | 回写计划 |
|--------|------------------------|----------------------|--------------------|----------|
| F39/F40 合约规模 | ZN 25吨/乘数25；NI/SN 1吨/1；SI 5吨/5 | ZN 5t（归一口径） | 快照以 A 档为准已冻结（校验器按 A 档 0 误差执行）；C 稿 5t 为归一显示口径，**非快照取值** | 主循环按交易所最新规格书逐品种复核 F39/F40 → 回写 V86.9-<SYM>-R2/RELEASE（J21 闭环） |
| F42/F43 涨跌幅 | ZN ±4/±6、NI ±4/±6、SN ±3/±5、SI ±4/±6 | LIMIT：NI ±5/±10、SN ±5/±10、SI ±4/±8、ZN ±4/±8 | 双轨固化：事件行以 A 档（CHECK-2 校验），巡检 LIMIT 阈值以 C 表（CHECK-2 对照） | 同上传新槽位（J21 闭环）；双轨口径写入告警日志基线变更事件 |

### 4.2 J22（25 vs 27 风险码）双源对账统一（本工单完成度：口径固化 + 巡检绑定）

- 事实：C 侧 flag 注记 25 项（4 CRITICAL/7 HIGH/12 MEDIUM/4 LOW）vs CSV 实表 `v869c_3way_risk_code_mapping.csv`（d9d64fea）27 行（DRI-001..011 / ALIGN-001..012 / SCHED-001..004）。
- 口径（沿用 J22 冻结）：**D 侧巡检以 CSV 实表 27 行为载入**；工单口径 25 项注记保留；`ALARM-J22-RISK-*` 监控"实表恒 27 行 + 条目一致性"。
- 统一路径：主循环以 A-SYN 风险编码映射（64f64110）+ C 实表（d9d64fea）双源对账 → 统一后基线更新（J22 闭环），本工单已登记告警阈值（§3）。

## 5. TRG-02 C-DEV manifest 入链准备（P2-2）

- 目标：C-DEV 流水线最终 manifest 落地且连续 3 次巡检 md5 不变 → 自动 PRE-ANCHOR 提议 → 人工确认后按实测入链（FINAL 链 C 支路 PENDING → VERIFIED）。
- 本工单产出：ME-06 C-DEV 绑定登记（§3）+ deploy package 稳定度轮询检查项（连续 3 次 md5 不变 → ALARM-CDEV-STABLE 提议）+ 入链动作脚本说明（锚点登记遵循 R1~R6，命名空间 `<SIDE>:<JOB>[:<SYM>]`，入链后链拓扑 5/5 一致复核）。
- 前置依赖：C 侧最终 manifest 落地（当前 0b9613fa→f4df4e4c→a695bc89 变化中，属开发预期）。

## 6. 证据绑定

| 引用 | 路径 | MD5 / 说明 |
|------|------|------------|
| 前置加固主报告 | dshd_arch_gap_enhance\DSHD_Architecture_Gap_Enhance_Report.md | B3FFA6156575DBF4C34D2D24DD190511（只读） |
| 监控增强规范 | dshd_arch_gap_enhance\monitor_enhance_spec.md | BCA7B9194A5D5E45440FD0AC37050781（只读） |
| 链残差实测（CHAIN-001） | v868_d_baseline_monitor\v868_d_delivery_link_status.csv | CHAIN-001 WARN 3/4（历史取证，零改动） |
| 链残差告警记录 | v868_d_baseline_monitor\v868_d_delivery_link_alarms.csv | ALARM-CHAIN-001 ×5（MEDIUM，零改动） |
| 权威 manifest（VALIDATE 声明） | v867df_validate\acd_v867df_delivery_manifest.md5 | 1df980287786c2598dcb151b40bfa306（JOB_READY.flag=c359ab98 声明源） |
| live CLOSE 重写 flag | v867df_validate\JOB_READY.flag | fa9fc4399e1c49683cd23e9fba5348dd（约定重写实证，零改动） |
| 终检台账（J21/J22 口径） | v869_multi_comm_final_debug\v869d_final_debug_ledger.md | J21 ARCHIVED / J22 ARCHIVED（只读引用） |
| 巡检规则（R01~R08 阈值） | v869_multi_comm_prep_syn\v869d_ad_acl_monitor_rule.md | R04 0 误差 / R02 P0 2h（只读引用） |
| 头寸验证自测输出 | position_verify_result.csv / position_verify_audit_log.csv | 12 行 / 12 行（本工单新增实测） |
| 版本锁惯例 | v869_d_zn_snapshot_ro_backup\SNAPSHOT_VERSION.lock | 12 字段（UPDATE_RULE 新槽位，只读引用） |

---

Generated by DSHD | JOB_ID DSHD-P0-MONITOR-ARCH-GATE-PREP | 2026-10-10T03:00:00+08:00 | SEED=42
