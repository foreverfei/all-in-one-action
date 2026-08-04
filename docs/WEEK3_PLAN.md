# Week 3：Action Competence 与真实 Directed Coupling Pilot

## 1. 本周目标

Week 3 不训练模型，不实现 planner、RL 或 interface learning。

本周只回答两个前置问题：

1. frozen InstructIR-7D 的 `denoise` 和 `deblur` action 是否能够在当前 noise–motion blur 数据上朝对应 oracle state 正确恢复；
2. 在 action 具备基本恢复能力后，`denoise -> deblur` 与 `deblur -> denoise` 是否仍存在不能由 predecessor mid error 单独解释的 directed coupling 差异。

研究链路固定为：

```text
Action competence
  -> 2-image real-model mini-pilot
  -> teacher semantic/integrity check
  -> DIV2K-20 full pilot
  -> clustered statistical analysis
  -> PASS / FAIL / REPEAT / STOP
```

只有 Week 3 Gate 通过，才讨论后续 coupling-aware training 或 successor-conditioned interface learning。

---

## 2. 固定实验边界

正式设置继续使用：

```text
Dataset: DIV2K validation，按文件名排序后的前 20 张
Preprocess: center crop 256×256
Degradations: Gaussian noise + linear motion blur
Noise sigma: 15 / 25 / 50
Blur length: 9 / 17
Blur angle: -30 / +30 degrees
Application order:
  noise -> motion_blur
  motion_blur -> noise
Model: frozen InstructIR-7D
Actions:
  denoise
  deblur
Action orders:
  denoise -> deblur
  deblur -> denoise
Primary metric: mean Charbonnier distance, epsilon = 1e-3
Secondary metrics: PSNR / LPIPS / DISTS
```

配置、prompt 和 coupling 定义分别以以下文件为准：

```text
docs/EXPERIMENT_PROTOCOL.md
configs/pilot_noise_blur.yaml
shared/action_prompts.yaml
```

本周禁止：

- 更换正式数据集、checkpoint、prompt、action pair 或 primary metric；
- 根据 Pilot 结果修改退化强度范围；
- 将 mock executor 结果作为科学证据；
- 提前训练 InstructIR、增加 loss、实现 predictor、planner、PPO 或 IQL；
- 只汇报总体均值而不保留逐样本和逐 path 结果。

如正式设置必须改变，先在教师 Issue 中说明原因，并使用新的 experiment ID。

---

## 3. Action Competence 定义

对于 predecessor action `i`：

```text
source_error_i
  = d(source, oracle_mid_i)

actual_mid_error_i
  = d(actual_mid_i, oracle_mid_i)

relative_recovery_i
  = (source_error_i - actual_mid_error_i)
    / (source_error_i + 1e-8)
```

解释：

```text
relative_recovery > 0   action 朝正确 oracle state 改善
relative_recovery = 0   action 没有产生有效恢复
relative_recovery < 0   action 使对应目标状态更差
```

必须分别报告：

```text
denoise relative recovery
deblur relative recovery
不同 noise sigma 下的恢复能力
不同 blur length / angle 下的恢复能力
两种 degradation application order 下的恢复能力
```

Action competence 是后续 coupling 分析的前置条件，不能用 final two-step quality 替代。

---

## 4. Line A：真实数据、模型与 Rollout

长期分支：

```text
student-a
```

### 4.1 开始前

- 同步最新 `main`；
- 固定 InstructIR 官方仓库 commit；
- 记录 image checkpoint 和 LM-head checkpoint 的文件名与 SHA256；
- 确认 `eval5d.yml`、prompt 文件和 Pilot config 未被修改；
- 记录 Python、PyTorch、CUDA、GPU 和关键依赖版本。

### 4.2 Mini-pilot

先只使用 DIV2K validation 排序后的前 2 张图像运行真实 InstructIR：

```text
2 images
× 3 noise levels
× 4 blur settings
× 2 degradation application orders
= 48 degradation programs
= 96 directed paths
```

必须提交：

- program/path 覆盖率；
- 失败、缺失和异常输出；
- 每个 action 的 relative recovery；
- 至少 4 组 source / oracle_mid / actual_mid 可视化；
- 至少 2 组完整 actual/oracle two-step path；
- 单条结果对应的 config、checkpoint、prompt、commit 和 metadata；
- 运行时间和峰值显存。

教师确认 action 语义、oracle state 和 metadata 正确后，才运行完整 20 张 Pilot。

### 4.3 Full pilot

完整 Pilot 目标：

```text
20 clean images
480 degradation programs
960 directed action paths
```

最低交付：

```text
outputs/pilot_noise_blur/week2_integrity_report.json
outputs/pilot_noise_blur/analysis/directed_coupling.csv
完整 metadata 与失败日志
student_A_week3.md 或 Issue 结果总结
```

Line A 不负责解释统计显著性，但必须保证每条 path 可追溯、可重现、无静默缺失。

---

## 5. Line B：Competence、方向差异与误差控制

长期分支：

```text
student-b
```

### 5.1 Action competence

新增逐 path 或逐 predecessor state 的 competence 表，至少包含：

```text
experiment_id
clean_id
program_id
action
source_error
actual_mid_error
relative_recovery
noise_sigma
blur_length
blur_angle_deg
application_order
```

输出：

```text
outputs/pilot_noise_blur/analysis/action_competence.csv
outputs/pilot_noise_blur/analysis/action_competence_summary.csv
```

### 5.2 统计单位

同一张 clean image 产生的多个参数组合不视为独立样本。

所有置信区间和显著性分析必须使用：

```text
cluster unit = clean_id
```

禁止把 960 条 path 当作 960 个独立样本进行普通 IID bootstrap。

### 5.3 Paired direction analysis

对同一 `program_id` 的两个 restoration directions 做配对比较：

```text
delta_direction
  = coupling(denoise -> deblur)
    - coupling(deblur -> denoise)
```

输出 image-cluster bootstrap 的：

```text
mean paired difference
median paired difference
95% confidence interval
direction win rate
```

### 5.4 Mid-error control

不能在两个方向内分别独立分箱后直接比较。

至少完成一种正式控制分析：

```text
signed_coupling
  ~ direction
  + mid_error
  + noise_sigma
  + blur_length
  + blur_angle
  + application_order
```

推断使用 `clean_id` cluster bootstrap。

同时输出共同 mid-error 支持区间内的匹配或共同分箱结果，避免两个方向的 error distribution 不重叠。

### 5.5 Secondary metric audit

在 primary Charbonnier coupling 之外，至少输出：

```text
actual_final_psnr
oracle_successor_psnr
psnr_excess

actual_final_lpips
oracle_successor_lpips
lpips_excess

actual_final_dists
oracle_successor_dists
dists_excess
```

Secondary metrics 用于稳健性复核，不替代 primary coupling 定义。

最低交付：

```text
action_competence.csv
action_competence_summary.csv
directed_coupling.csv
directional_asymmetry.csv
mid_error_control.csv
secondary_metric_audit.csv
student_B_week3.md 或 Issue 结果总结
```

---

## 6. 教师检查

教师在 Week 3 只检查以下内容：

### Check A：Action 语义

- `denoise` 主要减少 Gaussian noise，而不是只做平滑或错误增强；
- `deblur` 主要改善 motion blur，而不是只做锐化或放大噪声；
- prompt、action 和输出文件方向映射一致。

### Check B：Counterfactual 语义

- `oracle_mid__denoise` 只保留 motion blur；
- `oracle_mid__deblur` 只保留 Gaussian noise；
- actual path、oracle successor 和 final target 没有错位；
- degradation application order 与 restoration action order 分开记录。

### Check C：统计有效性

- 置信区间以 `clean_id` 为 cluster；
- direction comparison 为同 program 配对；
- mid-error control 使用共同支持区间或显式回归控制；
- 负结果、失败条件和不确定性均被保留。

---

## 7. Week 3 Gate

### G0：工程与可追溯性

必须全部满足：

- 2-image mini-pilot 无静默缺失；
- full pilot 覆盖 480 programs 和 960 paths，或明确列出全部失败；
- Tensor 为 HWC float32 RGB `[0,1]`；
- source 和 oracle states 可由 metadata 重渲染；
- checkpoint SHA256、InstructIR commit、config、prompt 和本仓库 commit 可追溯；
- action/path mapping 抽查正确。

G0 不通过：

```text
REPEAT
```

### G1：Action competence

两个 action 分别满足：

```text
median relative_recovery > 0
positive recovery rate >= 0.60
```

并且不存在某个完整 severity 条件下几乎全部为负恢复。

若一个 action 明显无效：

```text
STOP 当前 baseline/action pair
```

优先重新评估 baseline、prompt 或退化匹配，不进入 coupling-aware method。

### G2：Coupling existence

至少一个方向满足：

```text
mean signed_coupling > 0
且 clean_id-cluster bootstrap 95% CI lower bound > 0
```

若两个方向均无稳定正 coupling：

```text
STOP 当前 coupling 主线
```

### G3：Independent direction/state effect

至少满足以下一项：

1. paired directional difference 的 clean-cluster bootstrap 95% CI 不跨 0；
2. 控制 `mid_error` 和退化参数后，direction effect 仍保持稳定且 CI 不跨 0；
3. 在共同 mid-error 支持区间内，两个方向仍表现出稳定差异。

若 G2 通过但 G3 不通过：

```text
FAIL interface-coupling claim
```

研究结论调整为普通 intermediate error propagation，后续只考虑 intermediate supervision 或 multi-step reconstruction，不主张 successor-conditioned interface。

### 最终决策

```text
PASS
  G0、G1、G2、G3 均通过；进入方法设计。

REPEAT
  工程、统计或样本覆盖不足，尚不能判断。

FAIL
  coupling 存在，但独立方向/状态效应不成立；调整研究主张。

STOP
  action competence 或 coupling existence 不成立；停止当前 action pair/baseline。
```

---

## 8. Issue 与提交要求

Week 3 使用新的阶段 Issue：

```text
[Line A][Week 3] Run real InstructIR competence and coupling pilot
[Line B][Week 3] Audit competence and controlled directional coupling
[Teacher][Week 3] Action competence and P1 scientific Gate
```

学生继续使用长期分支：

```text
student-a
student-b
```

每名学生在对应 Issue 中至少更新：

- mini-pilot 结果；
- full pilot 结果或阻塞；
- 关键数字和结果路径；
- 当前 commit；
- 失败、不确定性和建议 Gate。

PR 仅提交代码、配置、测试和小型结果摘要，不提交模型权重、数据集或完整大规模 outputs。

---

## 9. Week 3 结束后的允许动作

只有最终决策为 `PASS`，下一阶段才允许讨论：

```text
Mid-only supervision
Mid + Path supervision
coupling-aware excess loss
successor-conditioned interface regularization
```

Week 3 不预先固定具体方法结构。方法选择必须由 competence、direction effect、mid-error control 和 failure cases 的真实结果决定。
