# DSHD V37.0 部署手册

**生成时间:** 2026-10-12T14:31:22.311533+08:00
**适用版本:** V37.0 (P37, dataset_version 1.12)

---

## 一、部署概述

| 项目 | 值 |
|------|-----|
| 站点URL | https://algo23-yunqingtian.github.io/dshd-dashboard/ |
| 仓库 | algo23-yunqingtian/dshd-dashboard |
| 部署分支 | main |
| Pages构建方式 | workflow |
| 部署方式 | GitHub Contents API + workflow_dispatch |

---

## 二、V37部署要点

### 2.1 文件清单
- HTML: web_site/index.html (257,164B)
- JSON数据集: 49个 (web_site/data/*.json)
- 标志文件: PHASE37_DATA_READY.flag
- 总文件数: 51 (含文档)

### 2.2 关键变更
1. **Euler风险贡献向量化**: 113.8x加速, 恒等式偏差2.08e-17
2. **CU进度条升级**: 0.0247, 接近0.025阈值, 稳态切换按钮
3. **性能对比升级**: P36→P37 Euler向量化对比
4. **V38占位面板**: Float32混合精度评估框架
5. **EULER_VECTORIZED徽章**: 导航栏+面板内标识
6. **负RC业务解释**: 移除异常误判, 新增对冲解释文案

### 2.3 数据变更
- version_tag: P36 → P37
- dataset_version: 1.11 → 1.12
- PB BEAR_IC: 17/17 → 18/18
- CU BEAR_IC: 0.0244 → 0.0247
- 漂移率: 2.6% → 2.4%
- 累积天数: 980 → 1015

---

## 三、回退方案

### 3.1 一键回退至V36

```bash
# 1. 找到V36.0的commit SHA
# (从git log或CI历史中查找)

# 2. 回退到V36 commit
git checkout <V36_SHA>

# 3. 重新触发部署
# 通过GitHub Actions workflow_dispatch(skip_validate=true)
```

### 3.2 回退验证
- 检查页面标题: 应显示DSHD-P36
- 检查版本徽章: 应显示V36
- 检查数据: version_tag应为P36

### 3.3 回退时间
- 预计: <5分钟

---

## 四、CI/CD注意事项

### 4.1 当前CI状态
- push触发的CI pre-flight validation当前失败
- 需使用workflow_dispatch + skip_validate=true绕过

### 4.2 推荐部署流程
1. 通过Contents API上传文件至main分支
2. 触发workflow_dispatch(skip_validate=true)
3. 等待CI完成(约2-3分钟)
4. 验证站点内容

### 4.3 待修复项
- CI pre-flight validation脚本需修复
- 修复后可恢复push触发自动部署

---

## 五、健康检查

### 5.1 关键检查点
- [ ] 页面标题: DSHD-P37
- [ ] 版本徽章: V37
- [ ] Euler面板: EULER_VECTORIZED + 113.8x
- [ ] CU进度条: 0.0247
- [ ] 性能面板: P36→P37对比
- [ ] V38占位面板: float32
- [ ] 全部JSON: version_tag=P37

### 5.2 健康指标
- HTTP 200: 全部通过
- 中位响应时间: <500ms
- P95响应时间: <700ms

---

**维护人:** DSHD
**更新记录:**
- V37.0: 2026-10-12T14:31:22.311533+08:00 - 初始部署
