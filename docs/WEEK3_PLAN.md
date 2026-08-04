# Week 3：Action Competence 与真实 Directed Coupling Pilot

## 1. 启动条件与本周定位

Week 3 仅在 Week 2 `PASS` 后启动。

Week 2 已验证 counterfactual state、actual/oracle path 和 coupling 测量链路；Week 3 使用真实 frozen InstructIR-7D 回答：

1. `denoise` 和 `deblur` 是否能朝对应 oracle intermediate 正确恢复；
2. action 具备基本能力后，是否存在稳定 harmful coupling；
3. 两个 restoration directions 是否存在配对差异；
4. 控制 predecessor `mid_error` 后，direction/state effect 是否仍存在；
5. 结论是否对 Charbonnier、PSNR、LPIPS 和 DISTS 基本一致。

执行链路：

```text
Week 2 Measurement Gate PASS
  -> 2-image real-model mini-pilot
  -> teacher semantic/integrity check
  -> DIV2K-20 full pilot
  -> competence / coupling / controlled analysis
  -> PASS / FAIL / REPEAT / STOP
```

Week 3 不训练模型，不实现 planner、RL、dynamics model 或 interface learning。

---

## 2. 固定代码与模型设置

### 模型

```text
Model: frozen InstructIR-7D
Image checkpoint: external/InstructIR/models/im_instructir-7d.pt
LM-head checkpoint: external/InstructIR/models/lm_instructir-7d.pt
Official config: external/InstructIR/configs/eval5d.yml
Prompts: shared/action_prompts.yaml
Actions: denoise / deblur
Device: CUDA
```

开始实验前必须记录：

```text
InstructIR repository commit
image checkpoint SHA256
LM-head checkpoint SHA256
project repository commit
Python / PyTorch / CUDA / GPU
```

模型、checkpoint、prompt、action pair 或 primary metric 发生变化时必须使用新的 experiment ID。

### 数据与退化

```text
Dataset: DIV2K validation
Preprocess: center crop 256 × 256
Seed: 2026
Noise sigma: 15 / 25 / 50
Blur length: 9 / 17
Blur angle: -30 / +30 degrees
Application order:
  noise -> motion_blur
  motion_blur -> noise
Restoration order:
  denoise -> deblur
  deblur -> denoise
Primary metric: mean Charbonnier, epsilon = 1e-3
Secondary metrics: PSNR / LPIPS / DISTS
Cluster unit: clean_id
Bootstrap samples: 2000
```

### 配置

| 用途 | 配置 | 图像数 | programs | paths |
|---|---|---:|---:|---:|
| Mini-pilot | `configs/pilot_noise_blur_2img.yaml` | 2 | 48 | 96 |
| Full pilot | `configs/pilot_noise_blur.yaml` | 20 | 480 | 960 |

---

## 3. 基本执行命令

### 3.1 准备 2-image mini-pilot

```bash
python tools/prepare_image_split.py \
  --input-dir /datasets/DIV2K/DIV2K_valid_HR \
  --output-dir data_sources/div2k_valid_first2 \
  --count 2 \
  --offset 0 \
  --mode symlink

bash scripts/run_noise_blur_audit.sh \
  configs/pilot_noise_blur_2img.yaml \
  data_sources/div2k_valid_first2 \
  instructir
```

### 3.2 准备并运行 20-image full pilot

```bash
python tools/prepare_image_split.py \
  --input-dir /datasets/DIV2K/DIV2K_valid_HR \
  --output-dir data_sources/div2k_valid_first20 \
  --count 20 \
  --offset 0 \
  --mode symlink

bash scripts/run_noise_blur_audit.sh \
  configs/pilot_noise_blur.yaml \
  data_sources/div2k_valid_first20 \
  instructir
```

运行正式实验前必须确认对应 `data_root` 和 `output_root` 为空，禁止混合旧输出。

---

## 4. 实验清单

| 实验 ID | 实验名称 | 负责人 | 目的 |
|---|---|---|---|
| W3-E1 | Real-model mini-pilot integrity | Line A | 用 2 张图验证真实 InstructIR 链路 |
| W3-E2 | Action competence audit | Line B | 判断 denoise/deblur 是否具备基本能力 |
| W3-E3 | DIV2K-20 full rollout audit | Line A | 获取完整真实模型逐 path 数据 |
| W3-E4 | Coupling existence test | Line B | 判断 harmful coupling 是否稳定存在 |
| W3-E5 | Paired direction effect | Line B | 判断两个 restoration order 是否不同 |
| W3-E6 | Mid-error controlled effect | Line B | 区分方向效应与普通误差传播 |
| W3-E7 | Secondary metric robustness | Line B | 检查结论是否依赖 Charbonnier |
| W3-E8 | Severity/content failure audit | A + B | 定位现象的边界和失败条件 |

---

## 5. W3-E1：Real-model mini-pilot integrity

### 目的

在消耗完整 20-image 计算资源前，确认官方 InstructIR、checkpoint、prompt、数据和 rollout 语义能够在真实环境中正确运行。

### 参与数据

```text
DIV2K validation 前 2 张
48 degradation programs
96 directed paths
```

### 输出

```text
outputs/pilot_noise_blur_2img/week2_integrity_report.json
outputs/pilot_noise_blur_2img/rollouts/
outputs/pilot_noise_blur_2img/analysis/directed_coupling.csv
环境与 checkpoint 记录
```

### 分析

- 48 programs / 96 paths 覆盖完整；
- 无 NaN、Inf、shape/range 错误；
- checkpoint、prompt、config 和 commit 可追溯；
- 至少展示 4 组 `source / oracle_mid / actual_mid`；
- 至少展示 2 组完整 actual/oracle two-step path；
- 记录总运行时间、单 path 时间和峰值显存；
- 人工确认 `denoise` 不只是任意平滑，`deblur` 不只是放大噪声。

### 允许结论

```text
PASS：真实模型链路、action 映射和输出语义可接受，可以运行 20-image Pilot。
REPEAT：环境、checkpoint、prompt 或输出语义存在问题。
```

2-image 结果不能用于统计显著性结论。

---

## 6. W3-E2：Action competence audit

### 目的

判断两个 action 是否真正朝对应 oracle intermediate 改善。若 action 本身无效，后续 coupling 分析没有可解释性。

### 固定定义

对于 predecessor action `i`：

```text
source_error_i = d(source, oracle_mid_i)
actual_mid_error_i = d(actual_mid_i, oracle_mid_i)
relative_recovery_i
  = (source_error_i - actual_mid_error_i)
    / (source_error_i + 1e-8)
```

解释：

```text
relative_recovery > 0：朝正确 oracle state 改善
relative_recovery = 0：无有效恢复
relative_recovery < 0：对应目标状态变差
```

### 需要补充的代码

```text
lineB/scripts/build_action_competence.py
```

### 输出

```text
outputs/<experiment>/analysis/action_competence.csv
outputs/<experiment>/analysis/action_competence_summary.csv
```

逐条记录至少包含：

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

### 分析

分别报告：

- denoise / deblur 的 median relative recovery；
- positive recovery rate；
- image-level 分布；
- noise sigma、blur length、angle 和 application order 条件统计；
- 最差 10 个 predecessor states；
- 是否存在整个 severity 条件几乎全部为负。

### Gate

两个 action 分别满足：

```text
median relative_recovery > 0
positive recovery rate >= 0.60
```

### 允许结论

```text
PASS：两个 action 在当前协议上具备基本恢复能力。
STOP：任一 action 大面积无效；优先更换 baseline、prompt 或 action pair。
```

不能用 final two-step quality 替代 competence 验证。

---

## 7. W3-E3：DIV2K-20 full rollout audit

### 目的

生成用于科学 Pilot 的完整、逐 path、可追溯真实模型数据。

### 参与数据

```text
20 clean images
480 degradation programs
960 directed paths
```

### 输出

```text
outputs/pilot_noise_blur/week2_integrity_report.json
outputs/pilot_noise_blur/rollouts/
outputs/pilot_noise_blur/analysis/directed_coupling.csv
完整 metadata 与失败日志
```

### 分析

- expected / completed / failed program 数量；
- expected / completed / failed path 数量；
- 每个 clean_id、参数条件和方向的覆盖率；
- 无静默缺失、重复唯一键或旧结果混入；
- 随机抽查至少 8 组真实路径；
- 失败必须保留原始错误、环境和 program_id。

### 允许结论

```text
PASS：数据覆盖和追溯性足以进入统计分析。
REPEAT：覆盖不完整、输出混杂或路径语义存在疑问。
```

Line A 不负责判断显著性。

---

## 8. W3-E4：Coupling existence test

### 目的

判断至少一个方向是否存在稳定正向 predecessor-induced excess error。

### Primary 变量

```text
signed_coupling
harmful_coupling
```

### 统计设置

```text
cluster unit = clean_id
bootstrap samples = 2000
不得将 960 条 path 当作 960 个 IID 样本
```

需要补充或修正的代码：

```text
lineB/scripts/analyze_clustered_coupling.py
```

### 输出

```text
clustered_direction_summary.csv
image_level_coupling_summary.csv
```

### 分析

对两个方向分别报告：

- mean / median signed coupling；
- mean harmful coupling；
- positive rate；
- clean_id-cluster bootstrap 95% CI；
- image-level coupling 分布；
- 去除单张图后的 leave-one-image-out 稳定性。

### Gate

至少一个方向满足：

```text
mean signed_coupling > 0
cluster bootstrap 95% CI lower bound > 0
```

### 允许结论

```text
PASS：当前 baseline/action pair 存在稳定 harmful coupling。
STOP：两个方向均无稳定正 coupling，停止当前 coupling 主线。
```

---

## 9. W3-E5：Paired direction effect

### 目的

判断同一 degradation program 下，`denoise -> deblur` 和 `deblur -> denoise` 的 coupling 是否系统不同。

### 固定配对

```text
delta_direction
  = coupling(denoise -> deblur)
    - coupling(deblur -> denoise)
```

配对键：

```text
program_id
```

### 输出

```text
directional_asymmetry_clustered.csv
per_image_direction_effect.csv
```

### 分析

- mean / median paired difference；
- clean_id-cluster bootstrap 95% CI；
- direction win rate；
- image-level direction reversal；
- application order 分层结果；
- 固定顺序、随机顺序和 oracle 顺序的 final-error gap。

### 允许结论

```text
CI 不跨 0：存在可测的方向差异。
CI 跨 0：不能主张两个方向系统不同。
```

普通 final-quality order gap 不等同于 directed coupling 差异，二者必须分别报告。

---

## 10. W3-E6：Mid-error controlled effect

### 目的

区分：

```text
H1：普通 intermediate error propagation
H2：控制 mid_error 后仍存在 direction/state-dependent coupling
```

### 至少完成的模型

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

需要补充的代码：

```text
lineB/scripts/analyze_mid_error_control.py
```

### 共同支持分析

除回归外，还必须在两个方向共同的 mid-error 支持区间内完成至少一种：

```text
nearest-neighbor matching
common-bin comparison
propensity-style weighting
```

禁止在两个方向内分别独立 `qcut` 后直接比较不同分箱。

### 输出

```text
mid_error_control.csv
common_support_report.csv
```

### 分析

- direction coefficient 与 cluster CI；
- mid_error coefficient；
- 两个方向的 mid-error distribution overlap；
- common-support 样本比例；
- 匹配前后方向差异；
- leave-one-image-out 稳定性。

### 允许结论

| 结果 | 允许结论 |
|---|---|
| direction effect 稳定且 CI 不跨 0 | 支持独立 direction/state effect |
| coupling 存在但 direction effect 消失 | 仅支持普通 intermediate error propagation |
| common support 很低 | 证据不足，需 REPEAT 或调整分析 |

---

## 11. W3-E7：Secondary metric robustness

### 目的

检查主要结论是否只由 Charbonnier distance 定义产生。

### 需要补充的代码

```text
lineB/scripts/build_secondary_metric_audit.py
```

### 输出字段

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

### 分析

- Charbonnier coupling 与 PSNR/LPIPS/DISTS excess 的 Spearman 相关；
- 各指标下方向效应符号是否一致；
- 指标不一致的 program 和图像；
- 是否由边缘平滑、噪声放大或感知指标偏置导致。

### 允许结论

```text
一致：结论不依赖单一像素误差定义。
不一致：主张必须限定为 Charbonnier-based excess error。
```

Secondary metrics 用于稳健性复核，不替代 primary 定义。

---

## 12. W3-E8：Severity/content failure audit

### 目的

明确 coupling 和 action competence 在哪些内容、强度和 formation order 下成立或失败。

### 分析维度

```text
clean_id
noise_sigma
blur_length
blur_angle_deg
application_order
predecessor action
```

### 输出

```text
parameter_conditioned_summary.csv
failure_case_manifest.csv
至少 8 组典型成功/失败可视化
```

### 分析

- competence 与 coupling 是否随 severity 单调变化；
- 哪些图像内容产生方向反转；
- 哪个 application order 更容易产生 harmful coupling；
- 是否由单张图或单个参数条件主导总体结果；
- 最差案例是否来自 baseline 完全失效，而非 coupling。

### 允许结论

本实验只定义现象边界，不将 post-hoc 案例解释为因果机制。

---

## 13. 分工与最低交付

### Line A：`student-a`

```text
2-image mini-pilot
20-image full rollout
checkpoint/environment report
coverage and failure report
路径与 oracle 可视化
student_A_week3.md 或 Issue 总结
```

### Line B：`student-b`

```text
action_competence.csv
clustered_direction_summary.csv
directional_asymmetry_clustered.csv
mid_error_control.csv
common_support_report.csv
secondary_metric_audit.csv
student_B_week3.md 或 Issue 总结
```

### 教师

```text
检查 action 语义
检查 oracle/path 映射
检查 cluster unit 和 paired key
给出 PASS / FAIL / REPEAT / STOP
```

---

## 14. Week 3 结果总结格式

每个实验必须记录：

```text
实验 ID：
科学问题 / 假设：
代码 / config / commit：
模型与 checkpoint SHA256：
参与数据和有效样本数：
主要变量：
统计单位与分析方法：
关键结果和 CI：
失败案例与不确定性：
允许得出的结论：
建议 Gate：PASS / FAIL / REPEAT / STOP
```

不得只报告总体均值。

---

## 15. Week 3 Gate

### G0：工程与追溯

- mini-pilot 和 full pilot 无静默缺失；
- full pilot 覆盖 480 programs / 960 paths，或完整列出失败；
- Tensor、source/oracle、action/path mapping 正确；
- checkpoint SHA256、InstructIR commit、config、prompt 和本仓库 commit 可追溯。

### G1：Action competence

两个 action 均满足：

```text
median relative_recovery > 0
positive recovery rate >= 0.60
```

### G2：Coupling existence

至少一个方向满足：

```text
mean signed_coupling > 0
clean_id-cluster bootstrap 95% CI lower bound > 0
```

### G3：Independent direction/state effect

至少满足以下一项：

1. paired direction difference 的 cluster CI 不跨 0；
2. 控制 mid_error 和退化参数后 direction effect 的 CI 不跨 0；
3. 共同 mid-error 支持区间内方向差异稳定。

### 最终决策

```text
PASS
  G0、G1、G2、G3 均通过；允许进入 Formal audit 或方法设计。

FAIL
  G2 通过但 G3 不通过；结论调整为普通 intermediate error propagation，
  后续只考虑 intermediate supervision / multi-step reconstruction。

REPEAT
  覆盖、统计、共同支持或语义证据不足。

STOP
  action competence 或 coupling existence 不成立；停止当前 baseline/action pair。
```

只有 `PASS` 后才允许讨论：

```text
Mid-only supervision
Mid + Path supervision
coupling-aware excess loss
successor-conditioned interface regularization
```
