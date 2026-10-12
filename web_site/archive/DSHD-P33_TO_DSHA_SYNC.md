# DSHD-P33 → DSHA 同步文档

**生成时间:** 2026-10-12T14:31:22.311533+08:00
**来源:** DSHD-P33 V37.0
**目标:** DSHA-P37 (数据源)

---

## 一、V37.0看板就绪

### 已集成P37数据
| 数据文件 | 状态 | 说明 |
|----------|------|------|
| portfolio_backtest_7asset.json | ✅ 已集成 | 7品种组合回测 |
| portfolio_risk_contribution_timeseries.json | ✅ 已集成 | Euler向量化 |
| rolling_correlation_matrix.json | ✅ 已集成 | 多窗口相关矩阵 |
| pb_cu_gray_admission_status.json | ✅ 已集成 | PB/CU灰度准入 |
| version_index.json | ✅ 已集成 | P37 ACTIVE |
| p37_site_health.json | ✅ 已集成 | 站点健康检查 |

### 数据集验证
- 49个JSON数据集全部version_tag=P37 ✓
- dataset_version=1.12 ✓
- version_tag regex: ^P\d+$ ✓
- dataset_version regex: ^1\.\d+$ ✓

---

## 二、P38数据准备

### DSHA-P38预期交付
- 交付物: PHASE38_DATA_READY.flag
- 预计时间: 2029-12-03 (W141)
- 预计累积天数: 1050

### DSHD V38.0面板(已预留)
- Float32混合精度评估面板框架 ✅
- V38预览标签页 ✅
- 等待DSHA-P38输出数据填充

---

## 三、CI/CD状态

### 当前部署状态
- V37.0已上线: https://algo23-yunqingtian.github.io/dshd-dashboard/
- CI: workflow_dispatch(skip_validate=true) → success
- 注意: push触发的CI pre-flight validation当前失败, 需修复

### 下次部署
- 触发方式: workflow_dispatch(skip_validate=true)
- 预期耗时: <5分钟
- 回退时间: <5分钟

---

## 四、性能指标

| 指标 | V37.0值 |
|------|---------|
| Euler加速比 | 113.8x |
| 组合构建加速比 | 151.4x |
| 全流程耗时 | 1.031s |
| 内存占用 | 21.3MB |
| 数据集数量 | 49 |
| 页面标签 | 18 |

---

**同步状态:** READY
**接收方确认:** PENDING DSHA-P38
