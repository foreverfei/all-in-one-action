# Week 3：Action Competence 与真实 Directed Coupling Pilot

## 1. 启动条件与目标

Week 3 仅在 Week 2 `PASS` 后启动。

Week 2 已负责验证 counterfactual state、actual/oracle path 和 coupling 测量链路；Week 3 不再重复证明测量公式，而是使用真实 frozen InstructIR-7D 回答：

1. `denoise` 和 `deblur` 是否能朝对应 oracle intermediate 正确恢复；
2. action 具备基本能力后，两个 restoration directions 是否存在稳定 harmful coupling；
3. 控制 predecessor `mid_error` 后，direction/state effect 是否仍存在。

执行链路：

```text
Week 2 Measurement Gate PASS
  -> 创建独立 2-image mini-pilot config
  -> 真实 InstructIR mini-pilot
  -> 教师语义与追溯抽查
  -> DIV2K-20 full Pilot
  -> clean_id-cluster statistical analysis
  -> PASS / FAIL / REPEAT / STOP
```

Week 3 不训练模型，不实现 planner、RL、dynamics model 或 interface learning。

---

## 2. 固定实验边界

```text
Dataset: DIV2K validation
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
Restoration orders:
  denoise -> deblur
  deblur -> denoise
Primary metric: mean Charbonnier distance, epsilon = 1e-3
Secondary metrics: PSNR / LPIPS / DISTS
Cluster unit: clean_id
```

正式定义来源：

```text
docs/EXPERIMENT_PROTOCOL.md
configs/pilot_noise_blur.yaml
shared/action_prompts.yaml
```

禁止：

- 根据结果修改退化范围、prompt、metric 或 action pair；
- 在同一 experiment ID 中更换 checkpoint 或外部仓库版本；
- 将 960 条 path 当作 960 个 IID 样本；
- 用 non-commutativity 替代 directed coupling；
- 只汇报总体均值，不保留逐 image、program 和 path 结果；
- 在 Gate 前增加训练 loss 或方法模块。

---

## 3. Mini-pilot 配置

2-image mini-pilot 必须使用独立、可追溯的配置，不能直接把 full Pilot 的输出目录复用为临时目录。

建议新增：

```text
configs/mini_pilot_noise_blur.yaml
```

它与 full Pilot 保持相同模型、prompt、退化和 metric，仅修改：

```text
experiment.id: mini_pilot_div2k_noise_blur_instructir7d
project.expected_clean_count: 2
project.data_root: data/mini_pilot_noise_blur
project.output_root: outputs/mini_pilot_noise_blur
```

准备 DIV2K 前 2 张：

```bash
python tools/prepare_image_split.py \
  --input-dir /datasets/DIV2K/DIV2K_valid_HR \
  --output-dir data_sources/div2k_valid_first2 \
  --count 2 \
  --offset 0 \
  --mode symlink
```

mini-pilot 规模：

```text
2 images
× 3 noise levels
× 4 blur settings
× 2 application orders
= 48 programs
= 96 directed paths
```

只有教师确认 action、oracle 和 metadata 语义正确后，才运行 full Pilot。

---

## 4. Action Competence

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
relative_recovery = 0   action 没有有效恢复
relative_recovery < 0   action 使目标状态更差
```

必须分别报告：

```text
denoise competence
deblur competence
noise sigma 条件结果
blur length / angle 条件结果
application order 条件结果
```

Action competence 不能用 two-step final quality 替代。

---

## 5. Line A：真实模型、数据与 Rollout

长期分支：

```text
student-a
```

### 5.1 环境与追溯

开始前记录：

```text
InstructIR repository commit
image checkpoint filename + SHA256
LM-head checkpoint filename + SHA256
eval5d.yml hash
prompt file hash
本仓库 commit
Python / PyTorch / CUDA / GPU
```

确认：

- `student-a` 已同步最新 `main`；
- mini/full config 使用独立 experiment ID 和输出目录；
- 旧输出未与当前实验混合；
- 所有正式推理使用 float32 Tensor，不通过 PNG/JPEG 中间量计算指标。

### 5.2 Mini-pilot

提交：

- 48 programs / 96 paths 覆盖率；
- 失败、缺失、NaN、越界和异常输出；
- action competence 逐条结果；
- 至少 4 组 `source / oracle_mid / actual_mid`；
- 至少 2 组完整 actual/oracle two-step path；
- 单条 path 对应的 config、checkpoint、prompt、commit 和 metadata；
- 总运行时间、每 path 时间和峰值显存。

### 5.3 Full Pilot

准备 DIV2K 前 20 张：

```bash
python tools/prepare_image_split.py \
  --input-dir /datasets/DIV2K/DIV2K_valid_HR \
  --output-dir data_sources/div2k_valid_first20 \
  --count 20 \
  --offset 0 \
  --mode symlink
```

运行：

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/pilot_noise_blur.yaml \
  data_sources/div2k_valid_first20 \
  instructir
```

目标规模：

```text
20 clean images
480 degradation programs
960 directed paths
```

Line A 最低交付：

```text
integrity report
完整 manifest 和 metadata
逐 program/path 失败记录
真实 rollouts
checkpoint / environment report
student_A_week3.md 或 Issue 总结
```

Line A 不负责统计显著性，但必须保证无静默缺失和路径可追溯。

---

## 6. Line B：Competence 与受控 Coupling 分析

长期分支：

```text
student-b
```

### 6.1 Action competence 表

至少包含：

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
action_competence.csv
action_competence_summary.csv
```

### 6.2 Directed coupling 表

每条 path 保留：

```text
mid_error
successor_intrinsic_error
actual_path_error
signed_coupling
harmful_coupling
non_commutativity
raw degradation parameters
```

每个 `program_id` 必须恰好有：

```text
denoise -> deblur
deblur -> denoise
```

### 6.3 Cluster statistics

同一 clean image 下的多个参数组合不视为独立样本。

所有真实实验置信区间使用：

```text
cluster unit = clean_id
```

禁止普通 path-level IID bootstrap。

### 6.4 Paired direction analysis

```text
delta_direction
  = coupling(denoise -> deblur)
    - coupling(deblur -> denoise)
```

输出：

```text
mean paired difference
median paired difference
clean_id-cluster bootstrap 95% CI
direction win rate
```

### 6.5 Mid-error control

至少实现：

```text
signed_coupling
  ~ direction
  + mid_error
  + noise_sigma
  + blur_length
  + blur_angle
  + application_order
```

推断使用 clean cluster bootstrap。

同时检查共同 mid-error 支持区间，不能把两个方向内部独立 `qcut` 后的分箱直接视为 matched comparison。

### 6.6 Secondary metric audit

至少输出：

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

Line B 最低交付：

```text
action_competence.csv
action_competence_summary.csv
directed_coupling.csv
directional_asymmetry.csv
mid_error_control.csv
secondary_metric_audit.csv
student_B_week3.md 或 Issue 总结
```

---

## 7. 教师抽查

### Check A：Action 语义

- `denoise` 主要去除 Gaussian noise，而非只做过度平滑；
- `deblur` 主要改善 motion blur，而非只锐化并放大噪声；
- prompt、action、文件名和 metadata 方向一致。

### Check B：Counterfactual 语义

- `oracle_mid__denoise` 只保留 motion blur；
- `oracle_mid__deblur` 只保留 Gaussian noise；
- actual final、oracle successor 和 clean target 没有错位；
- application order 与 restoration direction 分开记录。

### Check C：统计有效性

- cluster unit 为 `clean_id`；
- direction comparison 为同 program 配对；
- mid-error control 使用显式控制和共同支持区间；
- 负结果、失败条件和不确定性均保留。

---

## 8. Week 3 Gate

### G0：工程与追溯

必须全部满足：

```text
mini-pilot 无静默缺失
full Pilot 覆盖 480 programs / 960 paths，或全部失败明确记录
Tensor 为 HWC float32 RGB [0,1]
source / oracle states 可重渲染
checkpoint、外部 commit、config、prompt 和本仓库 commit 可追溯
action/path mapping 抽查正确
```

不通过：

```text
REPEAT
```

### G1：Action competence

两个 action 分别满足：

```text
median relative_recovery > 0
positive recovery rate >= 0.60
```

且不存在完整 severity 条件下几乎全部负恢复。

一个 action 明显无效：

```text
STOP 当前 baseline/action pair
```

### G2：Coupling existence

至少一个方向满足：

```text
mean signed_coupling > 0
clean_id-cluster bootstrap 95% CI lower bound > 0
```

两个方向均无稳定正 coupling：

```text
STOP 当前 coupling 主线
```

### G3：Independent direction/state effect

至少满足一项：

1. paired directional difference 的 clean-cluster 95% CI 不跨 0；
2. 控制 `mid_error` 和退化参数后，direction effect 的 CI 不跨 0；
3. 共同 mid-error 支持区间内仍存在稳定方向差异。

G2 通过但 G3 不通过：

```text
FAIL interface-coupling claim
```

研究结论调整为普通 intermediate error propagation，后续只考虑 intermediate supervision 或 multi-step reconstruction。

### 最终决策

```text
PASS
  G0 / G1 / G2 / G3 全部通过；允许正式扩展和方法讨论。

REPEAT
  工程、统计或覆盖不足，尚不能判断。

FAIL
  coupling 存在，但独立 direction/state effect 不成立；调整 claim。

STOP
  action competence 或 coupling existence 不成立；停止当前 pair/baseline。
```

---

## 9. Issue 与提交

Week 2 PASS 后创建：

```text
[Line A][Week 3] Run real InstructIR competence and coupling pilot
[Line B][Week 3] Audit competence and controlled directional coupling
[Teacher][Week 3] Action competence and scientific Gate
```

Issue 至少更新：

- mini-pilot 结果；
- full Pilot 结果或阻塞；
- 关键数字和结果路径；
- 当前 commit；
- 失败、不确定性和建议 Gate。

PR 只提交代码、配置、测试、文档和小型结果摘要，不提交数据集、权重或完整大规模 outputs。

---

## 10. Week 3 后允许动作

只有 `PASS` 后才允许：

```text
运行 DIV2K-100
运行 Kodak24 / BSD100
增加 Restormer experts 对照
讨论 Mid-only / Mid+Path / coupling-aware candidate
```

Week 3 不预先固定最终方法。后续技术路线必须由 competence、coupling existence、direction effect、mid-error control 和 failure cases 的真实结果决定。
