# 正式实验协议

本文档固定 All-in-One Action 课题跨阶段共享的数据、baseline、退化、测量定义和科学 Gate。

周计划负责说明当周任务；本文件负责保证不同周次使用同一套正式定义。若数据集、checkpoint、prompt、action pair、primary metric 或 coupling 定义发生变化，必须先修改本协议并使用新的 experiment ID。

---

## 1. 主研究问题

当前只研究一组可控 action pair：

```text
Degradations: Gaussian noise + linear motion blur
Action 1: denoise
Action 2: deblur
```

需要依次回答：

1. counterfactual state、actual/oracle rollout 和 directed coupling 是否能够被正确测量；
2. frozen InstructIR-7D 的 `denoise` 和 `deblur` 是否具备基本 action competence；
3. `denoise -> deblur` 与 `deblur -> denoise` 是否产生稳定的 harmful coupling；
4. 控制 predecessor `mid_error` 后，direction/state effect 是否仍存在；
5. 若现象成立，后续方法能否在保持单步恢复质量的同时降低 harmful coupling。

不得从普通 final-quality order gap 直接推断存在 interface coupling。

---

## 2. 阶段边界

| 阶段 | 固定任务 | 可以得出的结论 |
|---|---|---|
| Week 1 | rollout、metrics、identity scaffold | 基础工程接口可运行 |
| Week 2 | counterfactual measurement protocol validation | oracle、path 和 coupling 测量可信 |
| Week 3 | 真实 InstructIR competence + DIV2K-20 Pilot | 判断现象是否具有科学研究价值 |
| Post-Week 3 formal audit | DIV2K-100 + Kodak24 / BSD100 | 判断现象是否跨内容和参数稳定 |
| Method stage | 根据 Gate 选择训练目标 | 判断 coupling 是否可被降低 |
| Generalization stage | unseen severity / pair / backbone | 判断方法是否依赖单一设置 |

关键限制：

```text
Week 2 PASS != real-model coupling成立
Week 3 PASS 才允许进入正式扩展或方法设计
```

---

## 3. Counterfactual 定义

对于由 noise 和 motion blur 组成的 source：

```text
source = D_blur(D_noise(clean))
或
source = D_noise(D_blur(clean))
```

两个 oracle intermediate 为：

```text
oracle_mid__denoise = D_blur(clean)
oracle_mid__deblur  = D_noise(clean)
```

对于有向 action path `i -> j`：

```text
actual_mid(i)
  = T_i(source)

actual_final(i -> j)
  = T_j(actual_mid(i))

oracle_successor(i -> j)
  = T_j(oracle_mid(i))

final_target
  = clean
```

所有路径必须保持同一 clean image、退化参数、noise realization 和 degradation application order。

---

## 4. 数据集与样本规模

### 4.1 Week 2 mock protocol validation

```text
2 mock clean images
× 3 noise levels
× 4 blur settings
× 2 application orders
= 48 degradation programs
= 96 directed paths
```

用途仅为工程、语义和数值 fixture 验证，不报告科学结论。

配置入口：

```text
configs/pilot_noise_blur.yaml
```

mock 模式会绕过正式 clean-image count，只复用正式参数网格。

### 4.2 Week 3 real-model mini-pilot

```text
DIV2K validation，按文件名排序后的前 2 张
2 × 3 × 4 × 2 = 48 programs
96 directed paths
```

mini-pilot 必须使用独立 experiment ID、data root 和 output root，不得与 20-image Pilot 混用结果。

建议配置文件：

```text
configs/mini_pilot_noise_blur.yaml
```

该配置需保持模型、prompt、参数网格和 metric 不变，仅将：

```text
expected_clean_count = 2
experiment.id = mini_pilot_div2k_noise_blur_instructir7d
```

并使用独立数据与输出目录。

### 4.3 Week 3 full Pilot

| 项目 | 设置 |
|---|---|
| 数据集 | DIV2K validation |
| 图像 | 按文件名排序后的前 20 张 |
| 预处理 | 短边不足 256 时等比例放大，然后中心裁剪 256×256 |
| 配置 | `configs/pilot_noise_blur.yaml` |
| programs | 20 × 3 × 4 × 2 = 480 |
| directed paths | 960 |

### 4.4 Post-Week 3 正式主实验

| 项目 | 设置 |
|---|---|
| 数据集 | DIV2K validation 全部 100 张 |
| 预处理 | 中心裁剪 256×256 |
| 配置 | `configs/formal_div2k_noise_blur.yaml` |
| programs | 2400 |
| directed paths | 4800 |

只有 Week 3 为 `PASS` 才运行。

### 4.5 内容分布外测试

| 数据集 | 图像数 | 配置 |
|---|---:|---|
| Kodak24 | 24 | `configs/ood_kodak24_noise_blur.yaml` |
| BSD100 | 100 | 主实验通过后新增配置 |

Kodak24 和 BSD100 不用于弥补 Week 3 Pilot 失败。

### 4.6 后续方法训练数据

仅在真实现象和独立 direction/state effect 均成立后使用：

```text
Train: DIV2K train 800 + Flickr2K 2650
Validation: DIV2K validation 100
Test: Kodak24 + BSD100
Patch: random 256×256
```

Week 2 和 Week 3 均不下载 Flickr2K、不训练模型。

---

## 5. 退化协议

### 5.1 Gaussian noise

```text
sigma ∈ {15, 25, 50}
noise std = sigma / 255
```

每个 parameter set 保存固定 noise seed。

同一 parameter set 的两个 degradation application orders 必须使用相同 noise realization，以避免把随机噪声差异误解释为 order effect。

### 5.2 Linear motion blur

```text
length ∈ {9, 17}
angle ∈ {-30°, +30°}
```

要求：

```text
normalized linear kernel
odd kernel size
reflect boundary mode
float32 computation
```

### 5.3 Degradation application order

每个参数组合均生成：

```text
noise -> motion_blur
motion_blur -> noise
```

必须与 restoration action order 分开记录：

```text
application_order
restoration_direction
```

二者禁止混用。

---

## 6. Baseline 与模型使用边界

### 6.1 正式主模型：Frozen InstructIR-7D

```text
Repository: mv-lab/InstructIR
Config: eval5d.yml
Image checkpoint: im_instructir-7d.pt
LM-head checkpoint: lm_instructir-7d.pt
State: fully frozen
Actions: denoise / deblur
Prompts: shared/action_prompts.yaml
```

每个真实实验必须记录：

```text
InstructIR repository commit
image checkpoint filename + SHA256
LM-head checkpoint filename + SHA256
config file hash
prompt file hash
本仓库 commit
Python / PyTorch / CUDA / GPU
```

更换 checkpoint、prompt 或外部仓库版本必须使用新 experiment ID。

### 6.2 可选跨架构对照

只有 InstructIR Pilot 通过后，才允许使用：

```text
Restormer color Gaussian denoiser
Restormer motion deblurring expert
```

将两个官方专家串联，判断 coupling 是否仅存在于共享 All-in-One 模型。

### 6.3 不纳入当前正式协议的方法

```text
PromptIR
OneRestore
CURE
其他未覆盖 noise–motion blur action pair 的 checkpoint
```

mock executor 仅用于 Week 2 和 CI，不得用于科学结论。

---

## 7. Metrics

### 7.1 Primary distance

```text
d(u, v) = mean(sqrt((u - v)^2 + epsilon^2))
epsilon = 1e-3
```

计算：

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
```

解释：

```text
signed_coupling > 0  predecessor residual 增加 successor final error
signed_coupling = 0  actual 与 oracle successor 等价
signed_coupling < 0  actual predecessor state 对 successor 更有利
```

### 7.2 Action competence

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
relative_recovery > 0  action 朝正确 oracle state 改善
relative_recovery = 0  无有效恢复
relative_recovery < 0  action 使目标状态更差
```

Action competence 是真实 coupling 分析的前置条件。

### 7.3 Secondary metrics

```text
PSNR
LPIPS
DISTS
non-commutativity
```

至少计算：

```text
actual_final metric
oracle_successor metric
excess metric difference
```

Secondary metrics 用于稳健性复核，不替代 primary coupling。

### 7.4 Non-commutativity

```text
non_commutativity
  = d(actual_final_i_to_j, actual_final_j_to_i)
```

它只表示两个最终输出不同，不等同于 predecessor-induced coupling。

---

## 8. 统计协议

### 8.1 独立单位

同一 clean image 产生的参数组合和 action paths 高度相关。

所有真实 Pilot 和正式实验的置信区间必须使用：

```text
cluster unit = clean_id
```

禁止将 960 条 Pilot paths 当作 960 个 IID 样本。

### 8.2 Paired direction comparison

同一 `program_id` 的两个 restoration directions 配对：

```text
delta_direction
  = coupling(denoise -> deblur)
    - coupling(deblur -> denoise)
```

输出：

```text
mean / median paired difference
clean_id-cluster bootstrap 95% CI
direction win rate
```

### 8.3 Mid-error control

至少完成一种正式模型：

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

同时检查共同 mid-error 支持区间，避免两个方向的 error distributions 不重叠。

两个方向内部独立 `qcut` 后直接比较不能作为正式控制结论。

---

## 9. 执行入口

### 9.1 Week 2 protocol validation

```bash
bash scripts/run_pilot_mock.sh configs/pilot_noise_blur.yaml
```

验证内容：

```text
deterministic degradation
counterfactual state rerender
actual/oracle rollout mapping
golden coupling fixtures
coupling table invariants
analysis script fixtures
pytest
```

### 9.2 准备 DIV2K-20 Pilot split

```bash
python tools/prepare_image_split.py \
  --input-dir /datasets/DIV2K/DIV2K_valid_HR \
  --output-dir data_sources/div2k_valid_first20 \
  --count 20 \
  --offset 0 \
  --mode symlink
```

### 9.3 Week 3 full Pilot

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/pilot_noise_blur.yaml \
  data_sources/div2k_valid_first20 \
  instructir
```

2-image mini-pilot 必须先使用单独的 mini config 和输出目录，不得将其结果写入 full Pilot root。

### 9.4 Post-Week 3 formal DIV2K audit

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/formal_div2k_noise_blur.yaml \
  /datasets/DIV2K/DIV2K_valid_HR \
  instructir
```

### 9.5 Kodak24 OOD

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/ood_kodak24_noise_blur.yaml \
  /datasets/Kodak24 \
  instructir
```

---

## 10. 输出与追溯

每个实验使用独立 `output_root`：

```text
rollouts/
analysis/
├── action_competence.csv
├── action_competence_summary.csv
├── directed_coupling.csv
├── directionality_summary.csv
├── directional_asymmetry.csv
├── state_dependence_report.csv
├── parameter_conditioned_summary.csv
├── mid_error_control.csv
├── secondary_metric_audit.csv
├── order_baseline_summary.csv
└── matched_error_analysis.csv
```

Week 2 当前脚本可能只生成其中的 coupling 与基础分析文件；Week 3 需补齐 competence、cluster statistics 和 secondary audit。

所有正式结果必须保存：

```text
experiment ID
config
prompt
model repository commit
checkpoint SHA256
本仓库 commit
raw degradation parameters
noise seed
application order
restoration direction
失败和缺失记录
```

禁止混合旧输出。实验开始前必须确认 data/output root 不包含其他 experiment ID 的残留文件。

---

## 11. Gates

### 11.1 Week 2：Measurement Gate

PASS 条件：

```text
48 mock programs / 96 paths 完整
source 与 oracle states 可精确重渲染
rollout mapping 正确
golden coupling fixtures 通过
coupling table 不变量通过
analysis fixtures 通过
pytest / mock pipeline 通过
```

Week 2 不判断真实 coupling 是否存在。

### 11.2 Week 3 G0：工程与追溯

```text
mini-pilot 无静默缺失
full Pilot 覆盖 480 programs / 960 paths，或全部失败明确记录
Tensor / metadata / checkpoint / commit 可追溯
action/path mapping 人工抽查正确
```

### 11.3 Week 3 G1：Action competence

两个 action 分别满足：

```text
median relative_recovery > 0
positive recovery rate >= 0.60
```

且不存在完整 severity 条件下几乎全部负恢复。

### 11.4 Week 3 G2：Coupling existence

至少一个方向满足：

```text
mean signed_coupling > 0
clean_id-cluster bootstrap 95% CI lower bound > 0
```

### 11.5 Week 3 G3：Independent direction/state effect

至少满足一项：

1. paired directional difference 的 clean-cluster 95% CI 不跨 0；
2. 控制 `mid_error` 和退化参数后，direction effect 的 CI 不跨 0；
3. 共同 mid-error 支持区间内仍有稳定方向差异。

### 11.6 Week 3 决策

```text
PASS
  G0 / G1 / G2 / G3 全部通过。

REPEAT
  工程、统计或覆盖不足，尚不能判断。

FAIL
  coupling 存在，但独立 direction/state effect 不成立；
  研究主张调整为普通 intermediate error propagation。

STOP
  action competence 或 coupling existence 不成立；
  停止当前 baseline/action pair。
```

只有 `PASS` 才运行 DIV2K-100、Kodak24，并讨论方法设计。

---

## 12. 后续方法边界

本协议暂不固定最终模型结构。

Week 3 PASS 后可以比较：

| 方法 | 目的 |
|---|---|
| Frozen baseline | 原始序列恢复行为 |
| Mid-only | 仅改善 intermediate quality |
| Mid+Path | 同时优化 intermediate 和 final path |
| Coupling-aware candidate | 显式降低 excess error 或提高 successor compatibility |

核心比较必须满足：

```text
single-step mid quality 基本相当
但 harmful coupling 和 final path error 更低
```

若 G2 通过但 G3 不通过，后续只允许研究 intermediate supervision 或 multi-step reconstruction，不主张 successor-conditioned interface coupling。
