# Week 2：Counterfactual Coupling 测量协议验证

## 1. 本周定位

Week 2 只验证实验测量链路是否正确，不使用真实 InstructIR 结果建立科学结论。

本周需要回答：

1. noise–motion blur 数据能否按固定参数和 seed 可复现生成；
2. counterfactual oracle states 是否满足预期语义并可由 metadata 精确重渲染；
3. actual/oracle rollout 的 action、方向和文件映射是否正确；
4. directed coupling、paired direction 和分析表是否通过人工可计算的 golden fixtures；
5. Line B 是否能独立读取 Line A 输出并得到一致结果。

固定阶段链路：

```text
Week 1：基础 rollout / metrics / identity scaffold
  -> Week 2：counterfactual measurement protocol validation
  -> Week 3：真实 InstructIR competence + DIV2K-20 scientific pilot
```

**Week 2 PASS 只表示测量协议可信，不表示真实模型上存在 directed coupling。**

---

## 2. 固定代码与数据设置

### 配置

```text
Config: configs/pilot_noise_blur.yaml
Week 2 executor: mock
Seed: 2026
Image size: 256 × 256
Tensor: HWC float32 RGB [0,1]
Primary distance: mean Charbonnier, epsilon = 1e-3
Actions: denoise / deblur
```

### 退化参数

```text
Gaussian noise sigma: 15 / 25 / 50
Motion blur length: 9 / 17
Motion blur angle: -30 / +30 degrees
Application order:
  noise -> motion_blur
  motion_blur -> noise
```

### 数据规模

```text
2 mock clean images
× 3 noise levels
× 4 blur settings
× 2 degradation application orders
= 48 degradation programs
= 96 directed action paths
```

### 基本命令

```bash
bash scripts/run_pilot_mock.sh configs/pilot_noise_blur.yaml
```

该命令依次执行：

```text
generate_week2_states
generate_week2_rollouts --executor mock
check_week2_integrity
build_week2_coupling_table
analyze_directionality
analyze_state_dependence
analyze_order_baselines
pytest
```

---

## 3. 实验清单

| 实验 ID | 实验名称 | 负责人 | 目的 |
|---|---|---|---|
| W2-E1 | Noise–blur parameter-grid determinism | Line A | 验证 48 个 program 可复现生成 |
| W2-E2 | Counterfactual oracle re-render | Line A | 验证 oracle state 定义与 metadata |
| W2-E3 | Directed rollout mapping fixture | Line A | 验证 actual/oracle path 无错位 |
| W2-E4 | Directed coupling golden fixture | Line B | 验证 coupling 数值定义 |
| W2-E5 | Coupling table integrity | Line B | 验证逐 path 表结构和唯一键 |
| W2-E6 | Paired/statistical script fixture | Line B | 验证方向配对与汇总脚本 |
| W2-E7 | A/B independent reproduction | A + B | 验证跨学生接口和结果一致性 |

---

## 4. W2-E1：Noise–blur parameter-grid determinism

### 目的

验证正式 noise–blur 参数网格、noise realization 和 application order 能被确定性生成。

### 参与数据

```text
2 mock clean images
12 parameter sets per image
2 application orders per parameter set
```

### 输出

```text
data/pilot_noise_blur/manifest.jsonl
data/pilot_noise_blur/programs/<program_id>/source.npy
data/pilot_noise_blur/programs/<program_id>/metadata.json
```

### 分析

- program count 必须为 48；
- 相同 config 和 seed 重跑后 source 数组完全一致；
- 每个 program 记录 noise sigma、noise seed、blur length、angle 和 application order；
- 同一 parameter set 的两个 application order 使用相同 noise realization；
- 两种 application order 的 source 不应被错误合并；
- 检查 dtype、shape、range 和 NaN/Inf。

### 允许结论

```text
PASS：参数网格、seed 和 source 生成可复现。
REPEAT：数量、seed 或 application-order 映射不一致。
```

本实验不判断合成退化是否覆盖真实世界分布。

---

## 5. W2-E2：Counterfactual oracle re-render

### 目的

证明 oracle intermediate 的定义正确，并可由 clean image 和 metadata 独立重建。

### 固定定义

```text
oracle_mid__denoise = 只保留 motion blur
oracle_mid__deblur  = 只保留 Gaussian noise
```

即：

```text
oracle_mid__denoise = D_blur(clean)
oracle_mid__deblur  = D_noise(clean)
```

### 自动分析

对每个 program 重新渲染：

```text
rerendered_source
rerendered_oracle_mid__denoise
rerendered_oracle_mid__deblur
```

Gate：

```text
max absolute error < 1e-7
```

### 人工抽查

至少检查 6 组：

```text
2 images × low / medium / high severity
```

每组展示：

```text
clean
source
oracle_mid__denoise
oracle_mid__deblur
```

### 允许结论

```text
PASS：counterfactual oracle state 语义与实现一致。
FAIL：oracle state 删除了错误退化、改变了非目标参数或无法重渲染。
```

---

## 6. W2-E3：Directed rollout mapping fixture

### 目的

验证 action_i、action_j、actual intermediate、actual final、oracle successor 和 reverse path 的文件映射。

### 固定关系

```text
actual_mid(i) = T_i(source)
actual_final(i -> j) = T_j(actual_mid(i))
oracle_successor(i -> j) = T_j(oracle_mid(i))
final_target = clean
```

### 基本代码设置

使用 deterministic mock executor，使 `denoise` 和 `deblur` 对数组产生可手工推导、互不相同的变换。若现有 mock 行为不足以识别方向，补充测试 fixture，不修改正式 action/coupling 定义。

建议测试文件：

```text
tests/test_week2_rollout_mapping.py
```

### 分析

- `denoise -> deblur` 与 `deblur -> denoise` 必须写入不同文件；
- 每个 program 恰好生成两个 direction；
- oracle successor 必须从对应 oracle mid 开始；
- reverse_actual_final 必须来自同一 program 的反向路径；
- application order 与 restoration action order 分开记录；
- 检查是否存在覆盖、重复或错误 join。

### 允许结论

```text
PASS：所有有向路径语义和文件映射正确。
FAIL：任一方向、oracle 或 reverse path 错位。
```

---

## 7. W2-E4：Directed coupling golden fixture

### 目的

使用人工可计算数组验证 coupling 数值实现，而不是只检查脚本能运行。

### 固定定义

```text
mid_error = d(actual_mid, oracle_mid)
successor_intrinsic_error = d(oracle_successor, clean)
actual_path_error = d(actual_final, clean)
signed_coupling = actual_path_error - successor_intrinsic_error
harmful_coupling = max(signed_coupling, 0)
```

### Golden fixtures

| Fixture | 设置 | 预期结果 |
|---|---|---|
| G0 Zero | `actual_mid=oracle_mid`，`actual_final=oracle_successor` | `signed=0`，`harmful=0` |
| G1 Harmful | `actual_path_error=0.20`，`successor_intrinsic=0.05` | `signed=0.15`，`harmful=0.15` |
| G2 Beneficial | `actual_path_error=0.03`，`successor_intrinsic=0.08` | `signed=-0.05`，`harmful=0` |

建议测试文件：

```text
tests/test_directed_coupling_golden.py
```

### Gate

```text
所有字段与手工结果误差 < 1e-7
```

### 允许结论

```text
PASS：coupling 数值定义实现正确。
```

`decomposition_error` 只验证内部恒等式，不能替代 oracle/path 语义验证。

---

## 8. W2-E5：Coupling table integrity

### 目的

验证逐 path 结果表的数量、唯一键、字段和可追溯性。

### 输出

```text
outputs/pilot_noise_blur/analysis/directed_coupling.csv
```

### 固定唯一键

```text
experiment_id
program_id
action_i
action_j
```

### 分析

```text
总行数 = 96
每个 program 行数 = 2
重复唯一键 = 0
NaN / Inf = 0
未知 action = 0
缺失 reverse direction = 0
无法追溯 metadata = 0
```

同一 program 的两个方向必须共享：

```text
clean_id
parameter_set_index
noise seed
noise sigma
blur length / angle
application order
```

### 允许结论

```text
PASS：逐 path coupling table 可用于后续真实模型分析。
REPEAT：存在重复、缺失、错配或不可追溯记录。
```

---

## 9. W2-E6：Paired/statistical script fixture

### 目的

验证 directionality、paired difference、state grouping 和 order baseline 脚本的分组逻辑。

### 人工表输入

至少构造 4 个 program，例如：

| Program | DN→DB coupling | DB→DN coupling |
|---|---:|---:|
| P1 | 0.20 | 0.10 |
| P2 | 0.30 | 0.15 |
| P3 | 0.10 | 0.05 |
| P4 | 0.40 | 0.20 |

预期 paired mean difference：

```text
mean([0.10, 0.15, 0.05, 0.20]) = 0.125
```

### 分析

- `directional_asymmetry.csv` 的 paired difference 与手工值一致；
- pivot index 不跨 program 错配；
- fixed/random/oracle order 使用同一组 program；
- parameter grouping 不丢失 severity 字段；
- mock bootstrap 数值只用于检查代码，不用于科学推断。

### 允许结论

```text
PASS：统计与分组脚本逻辑正确。
```

不能由 mock executor 的均值或 CI 判断真实 coupling 是否存在。

---

## 10. W2-E7：A/B independent reproduction

### 目的

验证 Line B 仅使用 Line A 冻结的 manifest、rollout arrays 和 metadata，即可独立重建 coupling table。

### 执行

1. Line A 生成并冻结 48-program 结果包；
2. Line B 不调用 Line A 内部生成函数，只读取约定接口；
3. 比较双方独立生成的 coupling 表。

### Gate

```text
row count 一致
unique key 一致
所有 primary 数值误差 < 1e-7
```

### 允许结论

```text
PASS：两条任务线的接口明确，可进入真实模型实验。
REPEAT：分析仍依赖隐式路径或 Line A 内部状态。
```

---

## 11. 分工与最低交付

### Line A：`student-a`

```text
48-program deterministic dataset
oracle re-render report
rollout mapping fixture
week2_integrity_report.json
至少 6 组 oracle 可视化
student_A_week2.md 或 Issue 总结
```

### Line B：`student-b`

```text
directed coupling golden tests
directed_coupling.csv
table integrity report
paired/statistical fixture report
student_B_week2.md 或 Issue 总结
```

---

## 12. Week 2 结果总结格式

每个实验必须记录：

```text
实验 ID：
目的：
代码 / config / commit：
参与数据：
预期输出：
实际输出：
关键检查数字：
失败与不确定性：
允许得出的结论：
建议 Gate：PASS / FAIL / REPEAT / STOP
```

---

## 13. Week 2 Gate

进入 Week 3 必须全部满足：

- W2-E1 48 programs 和 96 paths 数量正确且可复现；
- W2-E2 source/oracle re-render 最大误差 `<1e-7`；
- W2-E3 所有 direction、oracle 和 reverse path 映射正确；
- W2-E4 golden fixtures 全部通过；
- W2-E5 coupling table 无重复、缺失和错配；
- W2-E6 paired/statistical fixture 与手工结果一致；
- W2-E7 A/B 独立复现一致；
- `pytest -q` 和 `run_pilot_mock.sh` 通过。

最终决策：

```text
PASS：测量协议可信，进入 Week 3 真实 InstructIR Pilot。
REPEAT：工程、语义或 fixture 证据不足。
FAIL：核心 counterfactual/coupling 定义无法被当前实现正确表达。
STOP：仅在测量协议本身不可执行时使用。
```

Week 2 的正式总结只能表述为：

> Counterfactual state construction, directed rollout mapping, and coupling measurement passed engineering and semantic validation.

不得表述为：

> Directed coupling has been demonstrated in a real restoration model.
