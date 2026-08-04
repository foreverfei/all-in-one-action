# Week 1：基础数据、Rollout 与指标接口验证

## 1. 本周定位

Week 1 只建立可复现的工程基础，不使用本周结果支持论文科学结论。

本周需要回答：

1. controlled degradation 数据能否按固定 seed 重复生成；
2. frozen restoration executor 是否满足统一输入输出接口；
3. 单步与有序双步 rollout 是否完整、方向明确且可追溯；
4. PSNR、LPIPS、DISTS、gain、influence 和 exact identity 是否按统一协议计算。

本周禁止训练模型、实现 RL/planner，或根据 mock executor 数值讨论最佳 action order。

---

## 2. 固定代码与数据设置

### 配置

```text
Config: configs/week1_shared.yaml
Seed: 2026
Image size: 256 × 256
Tensor: HWC float32 RGB [0,1]
Actions: dehaze / derain / enhance
Degradation pairs:
  haze + rain
  haze + lowlight
  rain + lowlight
Identity threshold: 1e-5
```

### 数据

| 用途 | 数据 | 数量 | 是否可用于科学结论 |
|---|---|---:|---|
| CI / smoke | 程序生成的 mock clean images | 2 | 否 |
| 本周验收 | mock 或明确记录来源的 clean RGB images | 20 | 否，只验证工程链路 |

### 基本命令

```bash
python -m lineA.scripts.generate_week1_data \
  --config configs/week1_shared.yaml \
  --mock-clean-count 2

python -m lineA.scripts.generate_week1_rollouts \
  --config configs/week1_shared.yaml \
  --executor mock

python -m lineA.scripts.check_rollout_integrity \
  --config configs/week1_shared.yaml

python -m lineB.scripts.build_week1_labels \
  --config configs/week1_shared.yaml \
  --metrics psnr

python -m lineB.scripts.validate_identity \
  --labels outputs/week1/labels/identity_check.csv

pytest -q
```

LPIPS 和 DISTS 在对应依赖安装完成后使用同一输入协议补跑，不得通过 PNG/JPEG 中间文件计算。

---

## 3. 实验清单

| 实验 ID | 实验名称 | 负责人 | 目的 |
|---|---|---|---|
| W1-E1 | Deterministic degradation generation | Line A | 验证数据和参数可复现 |
| W1-E2 | Single/two-step rollout integrity | Line A | 验证 action path 与文件接口 |
| W1-E3 | Metric input contract | Line B | 验证指标范围、方向和数值接口 |
| W1-E4 | Gain/influence label construction | Line B | 验证逐样本标签计算链路 |
| W1-E5 | Exact two-step identity | Line B | 验证 action 顺序和标签索引无错位 |
| W1-E6 | A/B interface integration | A + B | 验证 Line B 可独立消费 Line A 输出 |

---

## 4. W1-E1：Deterministic degradation generation

### 目的

证明相同 clean image、config、参数和 seed 可以生成完全一致的 mixed-degradation input。

### 执行设置

```text
20 clean images
3 degradation pairs
每个样本保存 degradation parameters 和 seed
```

### 输出

```text
data/week1/
manifest
mixed inputs
metadata.json per sample
```

### 分析

- 相同 seed 重跑两次，比较数组；
- 检查 dtype、shape、range、NaN/Inf；
- 检查 metadata 中的 degradation pair、参数和 seed；
- 抽查 3 个样本确认退化方向符合配置。

### 允许结论

```text
PASS：数据生成可复现，metadata 足以重建输入。
REPEAT：存在非确定性、缺失参数或数组协议不一致。
```

不能由本实验判断退化是否具有论文级真实性。

---

## 5. W1-E2：Single/two-step rollout integrity

### 目的

证明每个 action 和有序 action pair 均生成独立、可追溯的输出。

### 数据规模

每张图像应生成：

```text
3 single-step outputs
6 ordered two-step outputs
```

20 张图像对应：

```text
60 single-step outputs
120 ordered two-step outputs
```

### 输出接口

```text
sample_id/
  input.npy
  dehaze.npy
  derain.npy
  enhance.npy
  dehaze__derain.npy
  derain__dehaze.npy
  ...
  metadata.json
```

### 分析

- 检查所有预期文件是否存在；
- 检查 `a -> b` 与 `b -> a` 使用不同路径名；
- 检查所有数组为 HWC float32 RGB `[0,1]`；
- 检查输出可追溯到 executor、checkpoint/config 和 commit；
- 保存至少 3 组完整恢复链用于人工检查。

### 允许结论

```text
PASS：rollout 文件完整，action order 和 metadata 映射正确。
REPEAT：存在覆盖、错位、缺失或静默失败。
```

mock 输出不得用于判断哪种 action order 更优。

---

## 6. W1-E3：Metric input contract

### 目的

统一 PSNR、LPIPS 和 DISTS 的输入范围与质量方向。

### 固定协议

```text
PSNR input: [0,1]，越高越好
LPIPS input: [-1,1]，越低越好
DISTS input: [0,1]，越低越好
Quality vector: [PSNR, -LPIPS, -DISTS]
```

### 分析

- identical image 的 PSNR 应达到实现允许的上限；
- identical image 的 LPIPS/DISTS 应接近 0；
- 人工加入更强扰动后，质量向量应整体下降；
- 检查 NaN、Inf、颜色通道和 batch 维处理。

### 输出

```text
metrics API tests
metric sanity report
```

### 允许结论

```text
PASS：三类指标的输入和方向统一。
REPEAT：指标对已知扰动方向响应错误或输入范围不一致。
```

---

## 7. W1-E4：Gain/influence label construction

### 目的

验证逐样本单步 gain 和有序双步 influence 标签能够稳定生成。

### 输出

```text
outputs/week1/labels/gain_labels.csv
outputs/week1/labels/influence_labels.csv
```

### 分析

- 每条记录必须包含 sample、action/order、metric、config 和 commit；
- 无 NaN、无重复唯一键、无缺失 action；
- 手工选择至少 2 个样本重算标签；
- 正、负 influence 各保留至少 3 个案例，检查是否来自正确路径。

### 允许结论

```text
PASS：标签公式、索引和逐样本记录正确。
```

本实验只验证 label pipeline，不证明真实 action interaction 存在。

---

## 8. W1-E5：Exact two-step identity

### 目的

通过代数恒等关系检查 action order、metric row 和文件索引是否一致。

### 输出

```text
outputs/week1/labels/identity_check.csv
```

### Gate

```text
max identity error < 1e-5
```

### 允许结论

```text
PASS：标签表内部计算和索引一致。
FAIL：存在公式实现、路径映射或 join key 错误。
```

identity 通过不代表科学现象成立，只代表内部计算自洽。

---

## 9. W1-E6：A/B interface integration

### 目的

验证 Line B 只依赖 rollout Tensor 和 metadata，即可独立完成所有标签计算。

### 执行

- Line A 生成并冻结一个小型结果包；
- Line B 在不调用 Line A 内部函数的情况下读取结果；
- 比较独立运行与一体化运行生成的 CSV。

### Gate

```text
row count 一致
unique key 一致
数值误差 < 1e-7
```

### 允许结论

```text
PASS：两条学生线可以低依赖并行推进。
REPEAT：接口仍依赖隐式路径或内部实现。
```

---

## 10. 分工与最低交付

### Line A：`student-a`

```text
数据生成代码和 manifest
单步/双步 rollout
integrity report
3 组恢复链可视化
student_A_week1.md 或 Issue 总结
```

### Line B：`student-b`

```text
metrics API
metric sanity tests
gain_labels.csv
influence_labels.csv
identity_check.csv
student_B_week1.md 或 Issue 总结
```

---

## 11. Week 1 结果总结格式

每名学生必须明确写出：

```text
实验 ID：
使用 config / commit：
参与数据：
实际输出数量：
关键检查数字：
失败或缺失：
本实验允许得出的结论：
建议 Gate：PASS / FAIL / REPEAT / STOP
```

---

## 12. Week 1 Gate

进入 Week 2 必须全部满足：

- W1-E1 数据确定性通过；
- W1-E2 rollout integrity 通过；
- W1-E3 metric contract 通过；
- W1-E4 标签表无缺失和重复；
- W1-E5 最大 identity error `<1e-5`；
- W1-E6 A/B 独立接口通过；
- `pytest -q` 通过；
- 所有结果可追溯到 config 和 commit。

最终决策：

```text
PASS：进入 Week 2 测量协议验证。
REPEAT：工程或接口证据不足。
FAIL：核心实现与协议不一致，需要重构。
STOP：仅在当前工程路线无法维护时使用。
```
