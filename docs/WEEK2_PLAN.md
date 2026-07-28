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

## 3. 教师统一配置

```text
Executor：frozen InstructIR
Actions：dehaze / derain / enhance
Degradations：haze / rain / lowlight
Clean images：20
Degradation pairs：3
Application orders per pair：2
Primary error：mean Charbonnier distance
Charbonnier epsilon：1e-3
Coupling decomposition threshold：1e-7
Output root：outputs/week2
```

学生不得自行修改 coupling 定义、primary error 或 action/degradation mapping。

## 4. Line A：Counterfactual Data & Rollout

### 保留 Week 1 代码

```text
lineA/degradations.py
lineA/executors/
lineA/scripts/generate_week1_data.py
lineA/scripts/generate_week1_rollouts.py
lineA/scripts/check_rollout_integrity.py
```

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

### Metadata 必须记录

```text
program_id
clean_id
degradation program
application order
parameters
seed
source degradations
action_i
action_j
executor
checkpoints
git commit
```

### Line A 最低交付

```text
120 source states
240 oracle intermediate states
240 actual intermediate outputs
240 actual ordered final outputs
240 oracle successor outputs
120 metadata files
outputs/week2/week2_integrity_report.json
reports/student_A_week2.md
```

### Line A Gate

- subset state 只删除指定退化；
- 其余退化参数和 seed 不变；
- 相对 application order 不变；
- actual/oracle 文件齐全；
- Tensor 为 HWC float32 RGB `[0,1]`；
- source 和 oracle subset 可由 metadata 精确重渲染。

## 5. Line B：Coupling Protocol & Analysis

### 保留 Week 1 代码

```text
lineB/metrics/quality_metrics.py
lineB/scripts/build_week1_labels.py
lineB/scripts/validate_identity.py
```

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

PSNR、LPIPS、DISTS 继续计算，但只作为 secondary metrics。

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

注意：`non_commutativity` 与 directed coupling 必须分别报告。

### State-dependence 分析

至少分析 coupling 与以下因素的关系：

```text
image content
degradation severity
degradation application order
mid_error
```

至少报告：

```text
conditional mean
conditional variance
Spearman correlation
bootstrap 95% CI
direction reversal rate
```

### Matched-error 分析

按 `mid_error` 分箱：

```text
low mid error
medium mid error
high mid error
```

验证相近 predecessor 单步误差下，directed coupling 是否仍有明显差异。

### Line B 最低交付

```text
outputs/week2/analysis/directed_coupling.csv
outputs/week2/analysis/directionality_summary.csv
outputs/week2/analysis/state_dependence_report.csv
outputs/week2/analysis/matched_error_analysis.csv
3 组高 coupling 案例
3 组低或负 coupling 案例
reports/student_B_week2.md
```

## 6. Mock smoke test

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

## 7. 每日节点

| 日期 | Line A | Line B | 教师检查 |
|---|---|---|---|
| Day 1 | degradation program 与 subset-state schema | Charbonnier error 与 coupling API | 锁定配置和 golden fixture |
| Day 2 | 同一 clean 生成完整 subset states | golden fixture 验证 | 检查 subset-state 语义 |
| Day 3 | actual path 与 oracle path rollout | 构建逐路径 coupling table | 检查 action direction mapping |
| Day 4 | 完成 120 programs 正式运行 | directionality 与 matched-error 分析 | 抽查失败样本与成本 |
| Day 5 | integrity report 与失败样本 | 统计报告、可视化与 P1 建议 | 给出 P1 Gate |

## 8. 自动测试

```text
tests/test_counterfactual_state_consistency.py
tests/test_directed_rollout_semantics.py
tests/test_coupling_decomposition.py
tests/test_degradation_order_metadata.py
```

必须检查：

1. 删除目标退化后，其余参数、seed 和相对顺序保持；
2. `a__b` 文件等于真实嵌套执行 `executor(executor(source,a),b)`；
3. `signed_coupling = actual_path_error - successor_intrinsic_error`；
4. `dehaze__derain` 与 `derain__dehaze` 不会错位。

## 9. P1 Gate

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
- non-commutativity 与 coupling 分开报告；
- secondary metrics 的方向无明显实现错误。

### P1-C：科学现象成立

至少满足：

1. 至少一个有向 pair 存在稳定正向 coupling；
2. 至少一个 pair 的两个方向显著不同；
3. matched mid-error 条件下仍存在 coupling 差异；
4. coupling 随图像、severity 或 application order 变化；
5. 不是所有样本都由固定方向占优。

若 P1-C 不通过：停止后续 interface learning，保留负结果或重新选择 action pair。

## 10. Issue、分支与 PR

### 当前 Issue

| 角色 | Issue |
|---|---|
| 学生 A | [#7](https://github.com/foreverfei/all-in-one-action/issues/7) |
| 学生 B | [#8](https://github.com/foreverfei/all-in-one-action/issues/8) |
| 教师 | [#9](https://github.com/foreverfei/all-in-one-action/issues/9) |

学生每日进展、阻塞和周末结果统一评论在对应主 Issue 下。

### 分支

```text
student-a/week2
student-b/week2
```

### PR 标题

```text
[Line A][Week 2] Add formal counterfactual state and rollout results
[Line B][Week 2] Add directed coupling audit results
```

PR 必须关联对应 Issue。

## 11. 本周不做

```text
不训练 dynamics predictor
不实现 latent transition model
不实现 planner
不实现 PPO / IQL / GRPO
不修改 InstructIR 参数
不删除 Week 1 gain/influence 代码
不将 non-commutativity 当作 directed coupling
```

## 12. Week 3 启动条件

只有 P1-A、P1-B、P1-C 全部通过，才复制 `WEEK_TEMPLATE.md` 创建：

```text
docs/WEEK3_PLAN.md
student-a/week3
student-b/week3
```

Week 3 候选目标：

```text
保持 predecessor 单步误差基本不恶化
同时降低 directed coupling
```

P1-C 未通过时，不创建 Week 3 interface-learning 代码。
