# Week 2：Counterfactual Directed Coupling Audit

> Week 1 的任务、接口、标签和 Gate 保持不变。Week 2 只新增反事实 subset states、actual/oracle path 和 directed coupling audit。

## 1. 本周目标

```text
degradation program
  -> counterfactual subset states
  -> actual path / oracle path
  -> error decomposition
  -> directed coupling audit
  -> P1 scientific Gate
```

本周不训练 InstructIR，不实现 predictor、planner、PPO 或 IQL。

## 2. 两套定义禁止混用

Week 1：

```text
gain / influence
= quality interaction diagnostics
```

Week 2：

```text
mid_error
successor_intrinsic_error
actual_path_error
signed_coupling
harmful_coupling
= predecessor-induced excess error audit
```

## 3. Line A：Counterfactual Data & Rollout

### 新增代码

```text
lineA/degradation_program.py
lineA/lattice_renderer.py
lineA/scripts/generate_week2_states.py
lineA/scripts/generate_week2_rollouts.py
lineA/scripts/check_week2_integrity.py
```

### 数据规模

正式设置：

```text
20 clean images
x 3 degradation pairs
x 2 degradation application orders
= 120 degradation programs
```

每个 program 保存：

```text
source.npy
clean.npy
oracle_mid__<action_i>.npy
actual_mid__<action_i>.npy
actual_final__<action_i>__<action_j>.npy
oracle_successor__<action_i>__<action_j>.npy
metadata.json
```

### Line A Gate

- subset state 只删除指定退化；
- 其余退化参数和 seed 不变；
- 相对 application order 不变；
- actual/oracle 文件齐全；
- Tensor 为 HWC float32 RGB `[0,1]`；
- source 和 oracle subset 可由 metadata 精确重渲染。

## 4. Line B：Coupling Protocol & Analysis

### 新增代码

```text
lineB/coupling/error_metrics.py
lineB/coupling/directed_coupling.py
lineB/scripts/build_week2_coupling_table.py
lineB/scripts/analyze_directionality.py
lineB/scripts/analyze_state_dependence.py
```

### Primary error

```text
d(u, v) = mean(sqrt((u - v)^2 + epsilon^2))
epsilon = 1e-3
```

### 每条有向路径

```text
mid_error
  = d(actual_mid, oracle_mid)

successor_intrinsic_error
  = d(oracle_successor, final_target)

actual_path_error
  = d(actual_final, final_target)

signed_coupling
  = actual_path_error - successor_intrinsic_error

harmful_coupling
  = max(signed_coupling, 0)

non_commutativity
  = d(actual_final_i_to_j, actual_final_j_to_i)
```

注意：non-commutativity 与 directed coupling 必须分别报告。

### Line B 最低交付

```text
outputs/week2/analysis/directed_coupling.csv
outputs/week2/analysis/directionality_summary.csv
outputs/week2/analysis/state_dependence_report.csv
outputs/week2/analysis/matched_error_analysis.csv
student_B_week2.md
```

## 5. Mock smoke test

```bash
python -m lineA.scripts.generate_week2_states \
  --config configs/week2_shared.yaml \
  --mock-clean-count 2

python -m lineA.scripts.generate_week2_rollouts \
  --config configs/week2_shared.yaml \
  --executor mock

python -m lineA.scripts.check_week2_integrity \
  --config configs/week2_shared.yaml

python -m lineB.scripts.build_week2_coupling_table \
  --config configs/week2_shared.yaml

python -m lineB.scripts.analyze_directionality \
  --config configs/week2_shared.yaml

python -m lineB.scripts.analyze_state_dependence \
  --config configs/week2_shared.yaml

pytest -q
```

预期 smoke-test 输出：

```text
2 clean images
12 degradation programs
24 directed paths
0 integrity failures
4 new Week-2 tests pass
```

## 6. 每日节点

| 日期 | Line A | Line B |
|---|---|---|
| Day 1 | degradation program 与 subset-state schema | Charbonnier error 与 coupling API |
| Day 2 | 同一 clean 生成完整 subset states | golden fixture 验证 |
| Day 3 | actual path 与 oracle path rollout | 构建逐路径 coupling table |
| Day 4 | 完成 120 programs 正式运行 | directionality 与 matched-error 分析 |
| Day 5 | integrity report 与失败样本 | 统计报告、可视化与 P1 Gate |

## 7. P1 Gate

### P1-A：数据正确

- 所有反事实状态可追溯；
- subset states 只删除目标退化；
- actual/oracle path 文件齐全；
- 相同 seed 结果一致；
- Tensor 为 float32 `[0,1]`；
- semantic rollout tests 全部通过。

### P1-B：Coupling 定义正确

- 所有 error/coupling 字段无 NaN；
- decomposition error `< 1e-7`；
- action order 映射正确；
- non-commutativity 与 coupling 分开报告。

### P1-C：科学现象成立

至少满足：

1. 至少一个有向 pair 存在稳定正向 coupling；
2. 至少一个 pair 的两个方向显著不同；
3. matched mid-error 条件下仍存在 coupling 差异；
4. coupling 随图像、severity 或 application order 变化；
5. 不是所有样本都由固定方向占优。

若 P1-C 不通过：停止后续 interface learning，保留负结果或重新选择 action pair。
