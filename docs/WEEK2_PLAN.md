# Week 2：Counterfactual Coupling 测量协议验证

## 1. 本周定位

Week 2 只验证实验测量链路是否正确，不使用真实 InstructIR 结果建立科学结论。

本周需要回答：

1. noise–motion blur 数据能否按固定参数和 seed 可复现生成；
2. counterfactual oracle states 是否满足预期语义并可由 metadata 精确重渲染；
3. actual/oracle rollout 的 action、方向和文件映射是否正确；
4. directed coupling、paired direction 和分析表是否通过人工可计算的 golden fixtures。

固定阶段链路：

```text
Week 1：基础 rollout / metrics / identity scaffold
  -> Week 2：counterfactual measurement protocol validation
  -> Week 3：真实 InstructIR competence + DIV2K-20 scientific pilot
  -> 后续：根据 Week 3 Gate 决定正式实验或方法设计
```

**Week 2 PASS 只表示测量协议可信，不表示 directed coupling 已经在真实模型上成立。**

---

## 2. 固定边界

Week 2 使用正式 noise–blur 参数定义，但默认只运行 mock/golden 验证：

```text
Degradations:
  Gaussian noise: sigma = 15 / 25 / 50
  Motion blur: length = 9 / 17
  Motion blur angle = -30 / +30 degrees
Application order:
  noise -> motion_blur
  motion_blur -> noise
Restoration actions:
  denoise
  deblur
Primary distance:
  mean Charbonnier, epsilon = 1e-3
```

默认 smoke 规模：

```text
2 mock clean images
× 3 noise levels
× 4 blur settings
× 2 degradation application orders
= 48 degradation programs
= 96 directed action paths
```

本周禁止：

- 使用 mock executor 数值判断 coupling 是否存在；
- 将 96 条 mock path 作为论文结果；
- 更换 action pair、coupling 定义或 primary distance；
- 训练 InstructIR、增加 loss、实现 planner、RL 或 interface learning；
- 只检查文件存在而不验证文件语义和方向映射。

旧 haze/rain/low-light 设置仅保留为历史工程 smoke，不属于当前论文主协议。

---

## 3. Line A：数据、Oracle 与 Rollout 语义

长期分支：

```text
student-a
```

### 3.1 数据生成

运行参数网格后必须得到：

```text
48 programs
96 directed paths
```

每个 program 至少记录：

```text
experiment_id
program_id
clean_id
noise sigma / seed
blur length / angle
application order
source path
oracle-mid paths
config
repository commit
```

必须验证：

- 相同 seed 重跑结果完全一致；
- Tensor 为 HWC float32 RGB `[0,1]`；
- 无 NaN、Inf 和静默缺失；
- 两种 application order 使用相同参数集合和对应 noise realization；
- `program_id` 唯一且能够追溯到全部生成参数。

### 3.2 Counterfactual oracle 语义

对于 noise + motion blur source：

```text
oracle_mid__denoise = 只保留 motion blur
oracle_mid__deblur  = 只保留 Gaussian noise
```

自动验证：

```text
source == rerender(full degradation program)
oracle_mid__denoise == rerender(blur only)
oracle_mid__deblur == rerender(noise only)
max_abs_error < 1e-7
```

人工抽查至少覆盖：

```text
2 张 mock image
× 轻 / 中 / 重不同参数条件
```

每组查看：

```text
clean
source
oracle_mid__denoise
oracle_mid__deblur
```

### 3.3 Rollout 映射

每条有向路径必须满足：

```text
actual_mid(i) = T_i(source)
actual_final(i -> j) = T_j(actual_mid(i))
oracle_successor(i -> j) = T_j(oracle_mid(i))
final_target = clean
```

使用具有可识别确定性行为的 mock executor 或 golden fixture，检查：

- `action_i` / `action_j` 没有交换；
- 两个方向不会覆盖同一文件；
- oracle-mid 没有读取错误；
- reverse path 与当前 path 正确配对；
- degradation application order 与 restoration action order 分开记录。

### Line A 最低交付

```text
week2_integrity_report.json
48-program manifest
oracle rerender check
rollout direction check
失败与缺失记录
student_A_week2.md 或 Issue 总结
```

---

## 4. Line B：Coupling 数值与分析脚本验证

长期分支：

```text
student-b
```

### 4.1 Directed coupling 定义

```text
mid_error
  = d(actual_mid, oracle_mid)

successor_intrinsic_error
  = d(oracle_successor, clean)

actual_path_error
  = d(actual_final, clean)

signed_coupling
  = actual_path_error - successor_intrinsic_error

harmful_coupling
  = max(signed_coupling, 0)

non_commutativity
  = d(actual_final_i_to_j, actual_final_j_to_i)
```

`non_commutativity` 与 `directed coupling` 必须分别报告。

### 4.2 Golden fixtures

至少实现以下三类人工可计算 fixture：

| Fixture | 条件 | 预期 |
|---|---|---|
| Zero | `actual_final = oracle_successor` | `signed=0, harmful=0` |
| Harmful | `actual_path_error > successor_intrinsic_error` | `signed>0, harmful=signed` |
| Beneficial | `actual_path_error < successor_intrinsic_error` | `signed<0, harmful=0` |

数值误差要求：

```text
absolute error < 1e-7
```

现有 `decomposition_error` 只作为实现一致性检查，不能替代 oracle、方向和文件语义验证。

### 4.3 Coupling 表不变量

`directed_coupling.csv` 必须满足：

```text
row count = 96
每个 program 恰好 2 个 restoration directions
唯一键 = experiment_id + program_id + action_i + action_j
重复唯一键 = 0
NaN / Inf = 0
缺失 reverse direction = 0
```

同一 program 的两个方向必须共享：

```text
clean_id
noise parameters and seed
blur parameters
application order
```

### 4.4 分析脚本 fixture

人为构造已知 direction difference 的小表，验证：

```text
directionality_summary.csv
directional_asymmetry.csv
state_dependence_report.csv
matched_error_analysis.csv
order_baseline_summary.csv
```

验收重点是分组、配对和字段正确，不解释 mock 数值的科学意义。

### Line B 最低交付

```text
golden fixture tests
directed_coupling.csv schema check
paired-direction fixture
analysis output validation
student_B_week2.md 或 Issue 总结
```

---

## 5. 执行入口

```bash
bash scripts/run_pilot_mock.sh configs/pilot_noise_blur.yaml
```

该命令只验证：

```text
noise / motion-blur operators
counterfactual lattice
actual / oracle rollout
integrity checks
coupling table
analysis script execution
unit tests
```

不得将输出中的 coupling 均值、方向差异或 order gap 用作科学结论。

---

## 6. 教师检查

### Check A：数据正确性

- 参数网格、seed 和 program 数量正确；
- source 与 oracle states 可重渲染；
- dtype、shape、range 和 metadata 正确。

### Check B：路径语义

- action 和 degradation 映射正确；
- actual/oracle path 没有错位；
- 两个 restoration directions 正确配对。

### Check C：数值实现

- Charbonnier 和 coupling golden fixtures 正确；
- 表结构、唯一键、配对和分析 fixture 正确；
- 失败、不确定性和已知限制完整记录。

---

## 7. Week 2 Gate

### PASS

以下条件全部满足：

```text
48 programs / 96 paths 完整或全部失败均有明确记录
source 和 oracle states 可精确重渲染
rollout action/path mapping 正确
golden coupling fixtures 全部通过
coupling table 不变量全部通过
分析脚本 fixture 全部通过
pytest 和 mock pipeline 通过
Line B 可独立读取 Line A 输出
```

允许结论：

> Counterfactual state construction, ordered rollout generation, and directed coupling measurement have passed engineering and semantic validation.

不允许结论：

> Directed coupling has been demonstrated on a real restoration model.

### REPEAT

出现以下任一情况：

```text
数量或 metadata 不一致
oracle state 无法重渲染
action/path mapping 不确定
golden fixture 失败
分析脚本配对错误
存在静默缺失
```

### STOP

只有 counterfactual 定义本身无法稳定构造或无法形成可审计测量接口时，才停止当前协议。

---

## 8. Issue 与分支

| 角色 | Issue | 分支 |
|---|---|---|
| Line A | [#7](https://github.com/foreverfei/all-in-one-action/issues/7) | `student-a` |
| Line B | [#8](https://github.com/foreverfei/all-in-one-action/issues/8) | `student-b` |
| 教师 | [#9](https://github.com/foreverfei/all-in-one-action/issues/9) | `main` |

学生在对应 Issue 中提交：

- 执行命令和 commit；
- 核心验证数字；
- 结果路径；
- 失败和限制；
- 建议 `PASS / REPEAT / STOP`。

---

## 9. Week 3 启动条件

只有 Week 2 为 `PASS`，才进入 [WEEK3_PLAN.md](WEEK3_PLAN.md)：

```text
真实 InstructIR action competence
-> 2-image mini-pilot
-> DIV2K-20 scientific pilot
-> clean_id-cluster statistical analysis
-> PASS / FAIL / REPEAT / STOP
```
