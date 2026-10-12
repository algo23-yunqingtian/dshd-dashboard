# FR-RISK-501 20 日窗自动再校准 Runbook (Recal Runbook)

| Property | Value |
|----------|-------|
| Job ID | DSHD-P3-AL-CU-PB-GRAY-PHASE4-GATE |
| Document ID | PHASE4-GATE-RUN-D2 |
| Fixed Slot | 2026-10-12T15:30:00+08:00 |
| Seed | 42 |
| Mode | V87-04 开发落地 - 501 20 日窗自动再校准流程 |
| Dependency | fr_risk_501_20d_recalibration_spec.md (b8699329..., READ-ONLY) + v87_04_playback_prep_checklist.md (1103a800..., READ-ONLY) + fr_risk_501_threshold_calibration_report.md (3b74c1ca..., READ-ONLY) |
| Authority | DSHD P3 Phase4 门禁 + FR-RISK 校准代理 |

## 1. 脚本就绪

- 回放脚本: `v87_04_playback.py`
  - `--mode r1r6`: V87-04-R1..R6 前置条件状态检查
  - `--mode replay`: position_verify real 模式三品种 dry-run (RISK-01/02 关闭逻辑)
  - `--mode recal`: 20 日窗阈值再校准
  - `--mode full`: 全部
- 演示窗口: `gate_prep_lab/v87_04_recal_window_demo.csv` (保守分布) /
  `gate_prep_lab/v87_04_recal_window_demo_b.csv` (偏高分布)

## 2. 统计方法 (沿 spec §3)

1. 每日计算 `bear_ratio_d = 空头记录数 / 总记录数` (side 列 BEAR/SHORT/SELL 分类);
2. 20 日分布 B = {b1..b20} (缺日顺延, 无缺口硬性);
3. `T_new = max(0.60, p90(B) + 0.10)` (保留保守下限, 叠加裕度);
4. 敏感性复核: 对 B 重算 FP@0.60 与 FP@T_new, 输出零误报实证.

## 3. 决策规则 (沿 spec §4, 脚本实测两分支)

| 情形 | 决策 | 实测 |
|------|------|------|
| p90(B)+0.10 <= 0.60 | MAINTAIN_0.60 (维持基线) | 场景 A: p90=0.35 -> T_new=0.60 -> MAINTAIN ✅ |
| 0.60 < T_new < 0.75 | ADOPT_T_NEW (采纳, 未触碰漏检边界) | 场景 B: p90=0.57 -> T_new=0.67 -> ADOPT ✅ |
| T_new >= 0.75 | REJECT_MAINTAIN (不采纳, 复盘) | 逻辑就绪 (0.75 漏检注入样本) |

两场景 FP@0.60=0, FP@T_new=0 (正常运营分布零误报).

## 4. 操作步骤 (真实窗口)

1. **前置全绿**: `v87_04_playback.py --mode r1r6` 输出 6/6 PASS
   (TD002 白名单锁 + 真实树 + real 回放; 当前 4/6, 数据未到项 PENDING);
2. **窗口采集**: 连续 20 个真实交易日头寸方向分布 -> `v87_04_recal_window_real.csv`
   (缺日顺延, 20 日无缺口);
3. **再校准**: `python v87_04_playback.py --mode recal --input <real_window>`
   -> 输出 T_new + decision + FP 复核;
4. **决策回写** (新槽位纪律, spec §5):
   - ADOPT: 回写 `fr_risk_501_508_mapping.json` (501 trigger) +
     `fr_risk_triggers_deploy.json` (TRG-FRRISK-501 阈值字段), 旧 0.60 归档只读;
   - MAINTAIN/REJECT: 维持 0.60, 记录复盘 (REJECT 时 0.75 漏检风险说明);
5. **验证**: T_new 生效后 7 日观察 (正常运营 FP=0, 注入/真实风险触发正常);
6. **回滚**: 新槽位回写旧阈值 0.60, 观察窗数据保留.

## 5. 联动

```
TD002 真实数据 -> 白名单锁 (R4) + 真实树 (R1) -> real 回放 (R2/R5/R6)
   -> 20 日窗采集 -> 501 再校准 (本 runbook) -> mapping/triggers 回写
   -> GATE-P2-01/02/03 转 PASS -> GATE-P2-APPROVED
```

## 6. 诚实披露

- 当前窗口数据为 lab 演示分布 (真实数据未到, TD002 阻塞), 统计方法与决策分支已实测;
- 真实 20 交易日窗口 + 回写需主循环在 TD002 数据就位后执行;
- 脚本已就绪, 数据依赖 PENDING 为已知状态非缺陷.

## 7. 证据绑定

| 引用 | 路径 | MD5 |
|------|------|-----|
| 回放+校准脚本 | v87_04_playback.py | (见复核表) |
| 演示窗口 A | gate_prep_lab/v87_04_recal_window_demo.csv | (见复核表) |
| 演示窗口 B | gate_prep_lab/v87_04_recal_window_demo_b.csv | (见复核表) |
| 20 日窗规范 (只读) | fr_risk_501_20d_recalibration_spec.md | b86993294859f3c6a6fa165d05e0946f |
| 校准基线 (只读) | fr_risk_501_threshold_calibration_report.md | 3b74c1cad5794cf3bae5aaebdbc56c74 |
