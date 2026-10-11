# DSHD-P26 -> P27 交接与复用说明

| 字段 | 值 |
|------|-----|
| 生成时间 | 2026-10-12T02:44:15+08:00 |
| 本阶段 | DSHD-P26 (数据源 DSHA-P31) |
| 看板版本 | V31.0 / VERSION_TAG=P31 / DATA_VERSION=1.8 |
| 下一阶段 | DSHD-P27 |
| 预期数据源 | DSHA-P32 (若上游继续滚动覆盖, 以实际可用最高相位为准) |

## 1. 相位无关化资产 (P27 可直接复用)

P26 已完成 CI 门禁的相位解耦, P27 换数据源时**不需要再改 deploy-pages.yml**:

| 资产 | 位置 | 说明 |
|------|------|------|
| 相位无关正则 | `.github/workflows/deploy-pages.yml` validate job | `P\d+` / `dataset_version 1.x` / `"version_tag": "P[0-9]+"` |
| shell 引号配平预检 | `D:\DSH_WORK\_p26_validate.py::quote_balance_precheck` | 剥离单引号段后计数未转义双引号, 奇数即 FAIL |
| bash -e 语义建模 | `D:\DSH_WORK\_p26_validate.py::run_step` | 仅链末命令失败才 abort, `&&` 链前缀失败豁免 |
| 本地全量 validate | `python D:\DSH_WORK\_p26_validate.py` | 51/51 steps PASS 为可发布前置 |
| 基线重算 | `python D:\DSH_WORK\_p26_make_baseline.py` | 从 LF git blob 重算, 自动排除 .bak |
| Contents API 发布 | `python D:\DSH_WORK\_p26_deploy.py` | github.com:443 不可达时的唯一可用发布路径 |
| 线上实测巡检 | `python D:\DSH_WORK\_p26_live_probe.py` | 需 `DSH_PAT` 环境变量 |

## 2. P27 最小改动清单

| # | 改动 | 位置 |
|---|------|------|
| 1 | `dataset_version` 1.8 -> 1.9, `version_tag` P31 -> P32 | `web_site/data/*.json` (43 文件) |
| 2 | index.html 顶部 V31.0 -> V32.0 + DSHA-P31 -> P32 文案 | `web_site/index.html` |
| 3 | 若新增/删除数据集, 更新 `dataset_index.json` files map + core_18 | `web_site/data/dataset_index.json` |
| 4 | 重算基线 (171 entries) | `web_site/data/MD5_BASELINE.json` |
| 5 | 实测重测线上巡检 | `web_site/data/p32_site_health.json` (新建, 沿用 P31 结构) |
| 6 | 删除旧 `p31_site_health.json` 的引用并确认其已下线 | `dataset_index.json` |
| 7 | 签发 `PHASE27_DONE.flag` + `phase27_gate_summary_report.md` + `vis_phase27_final_check.md` | 仓库根 |
| 8 | `web_deploy_manual.md` 追加 §26 | 仓库根 |

**不需要**改动 deploy-pages.yml (相位断言已解耦)。

## 3. 已知遗留 (P27 待办)

| 编号 | 项 | 严重度 |
|------|----|:------:|
| P1 | CU 灰度 6/14 未达标 (BEAR_IC 0.0234 < 0.025), 维持 1.5%% 仓位上限 | P1 |
| P1 | github.com:443 smart-HTTP push 不可达, 依赖 Contents API | P1 |
| P3 | deploy-pages.yml 部分 step **显示名**仍含 P23/P24 字样 (断言已相位无关) | P3 |
| P3 | cold 连接 max 15170ms (含 TLS 握手); warm 已达标 median 59ms | P3 |
| P3 | `git.status` 中本地 HEAD 与远端 head 相差 1 个 Contents API 提交 | P3 |

## 4. 发布节奏约定

Contents API 逐文件发布会在远端产生独立提交, 因此:

- 本地 HEAD 与远端 head 相差 1 个提交是**正常**的 (内容一致)
- 每个发布 run 对应一次 Contents API 发布, 3 次成功 run 分别对应:
  1. `38162816772` — 数据平面首版 + CI 相位解耦
  2. `38163555999` — PB/CU 准入状态与 dataset_index 修正
  3. `38164978839` — p31_site_health 实测重测
- 远端 head 领先时不要 `git push --force`, 直接以 Contents API 继续发布即可

## 5. 关键数值 (P27 基线对比用)

| 指标 | P26 终值 | 阈值 |
|------|:--------:|:----:|
| IC | 0.0586 | >= 0.0575 |
| IC 漂移率 | 3.6%% | < 4.8%% |
| 阻断 | FALSE | - |
| 解锁条件 | 6/6 MET | 6/6 |
| PB BEAR_IC | 0.0294 | >= 0.030 (14/14 达标) |
| CU BEAR_IC | 0.0234 | >= 0.025 (未达标) |
| VIF | 1.0065 | < 1.02 |
| MD5 基线 | 171 entries / 3,503,264 B | self-check 全匹配 |
| 线上 warm median | 59 ms | < 400 ms |
