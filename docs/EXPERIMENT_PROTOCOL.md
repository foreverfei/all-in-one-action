# 正式实验协议

本文档固定当前课题的数据集、baseline、退化参数和运行脚本。原有 Week 1/Week 2 的 haze/rain/low-light 配置继续作为工程 smoke test，不作为论文主结果。

## 1. 主研究问题

主实验只研究一组最容易解释的 action pair：

```text
noise + motion blur

Action 1: denoise
Action 2: deblur
```

需要回答：

1. `denoise -> deblur` 与 `deblur -> denoise` 是否产生不同的 directed coupling；
2. 这种差异是否在控制 predecessor 单步误差后仍存在；
3. coupling 是否随 noise sigma、blur length、blur angle 和 degradation application order 变化；
4. 后续 interface learning 能否在基本保持单步质量的同时降低 coupling。

## 2. 数据集

### 2.1 Pilot

| 项目 | 设置 |
|---|---|
| 数据集 | DIV2K validation |
| 图像 | 按文件名排序后的前 20 张 |
| 预处理 | 不缩放；若短边不足 256 才等比例放大；随后中心裁剪 256×256 |
| 配置 | `configs/pilot_noise_blur.yaml` |
| 程序数 | 20 × 3 noise × 4 blur × 2 application orders = 480 |
| directed paths | 960 |

### 2.2 正式主实验

| 项目 | 设置 |
|---|---|
| 数据集 | DIV2K validation 全部 100 张 |
| 预处理 | 中心裁剪 256×256 |
| 配置 | `configs/formal_div2k_noise_blur.yaml` |
| 程序数 | 100 × 3 × 4 × 2 = 2400 |
| directed paths | 4800 |

### 2.3 内容分布外测试

| 项目 | 设置 |
|---|---|
| 数据集 | Kodak24 |
| 图像 | 全部 24 张 |
| 配置 | `configs/ood_kodak24_noise_blur.yaml` |
| 程序数 | 24 × 3 × 4 × 2 = 576 |
| directed paths | 1152 |

第二个 OOD 数据集建议使用 BSD100，协议与 Kodak24 相同；在主实验跑通后再增加对应配置。

### 2.4 Week 3 训练数据

只有 directed coupling audit 通过后才使用：

```text
Train: DIV2K train 800 + Flickr2K 2650
Validation: DIV2K validation 100
Test: Kodak24 + BSD100
Patch: random 256×256
```

Week 2 不下载 Flickr2K，不训练模型。

## 3. 退化协议

### 3.1 Gaussian noise

```text
sigma ∈ {15, 25, 50}
noise standard deviation = sigma / 255
```

每个 program 保存独立 seed。相同 parameter set 的两个 application orders 使用相同 noise realization。

### 3.2 Linear motion blur

```text
length ∈ {9, 17}
angle ∈ {-30°, +30°}
```

使用归一化线性 motion-blur kernel，边界模式为 reflect。

### 3.3 Application orders

每个参数组合都生成：

```text
noise -> motion_blur
motion_blur -> noise
```

这两个 order 用于检查 degradation formation order 是否影响 action coupling。它们不能与 restoration action order 混为一谈。

## 4. Baseline 方法

### 4.1 当前必须运行

#### B0. Frozen InstructIR-7D

- 方法：InstructIR，ECCV 2024；
- 官方代码：`https://github.com/mv-lab/InstructIR`；
- image checkpoint：`im_instructir-7d.pt`；
- LM-head checkpoint：`lm_instructir-7d.pt`；
- config：`eval5d.yml`；
- 参数：全部冻结；
- prompts：`shared/action_prompts.yaml`；
- action order：同时运行 `denoise -> deblur` 和 `deblur -> denoise`。

B0 是 directed coupling audit 的主 baseline。

### 4.2 从 B0 结果直接派生的顺序对照

不需要额外模型：

| 名称 | 定义 |
|---|---|
| Fixed-DN-DB | 固定 `denoise -> deblur` |
| Fixed-DB-DN | 固定 `deblur -> denoise` |
| Oracle-Order | 对每个样本取两个顺序中 final error 更低者 |
| Random-Order | 固定随机种子，在两个顺序间均匀选择 |

这些对照只用于量化 order gap，不构成论文方法。

### 4.3 Week 3 方法消融

只有 Week 2 通过后实现：

| 方法 | 损失 |
|---|---|
| B0 Frozen | 原始 InstructIR，不训练 |
| B1 Mid-only | `L_mid` |
| B2 Mid+Path | `L_mid + L_path` |
| Ours | `L_mid + L_excess + L_interface` |

核心比较必须满足：

```text
single-step mid error 基本相当
但 Ours 的 harmful coupling 更低
```

### 4.4 后续外部方法对照

以下方法不阻塞当前 pilot：

1. **Restormer experts**：官方 Gaussian color denoiser + motion deblurring model，作为分离任务模型链的对照；
2. **PromptIR**：作为 blind one-shot AiO final-restoration reference，只报告最终质量，不参与 action-specific coupling 定义。

在没有完成统一 float32 wrapper 前，不允许通过 PNG 中间文件调用这些 baseline。

## 5. Primary 和 secondary metrics

### Primary

```text
mean Charbonnier distance, epsilon = 1e-3
```

计算：

```text
mid_error
successor_intrinsic_error
actual_path_error
signed_coupling
harmful_coupling
```

### Secondary

```text
PSNR
LPIPS
DISTS
non-commutativity
```

PSNR/LPIPS/DISTS 用于结果复核，不用于替代 directed coupling 分解。

## 6. 环境准备

### 6.1 InstructIR

```bash
mkdir -p external
git clone https://github.com/mv-lab/InstructIR.git external/InstructIR
```

按 InstructIR 官方 README 下载：

```text
external/InstructIR/models/im_instructir-7d.pt
external/InstructIR/models/lm_instructir-7d.pt
```

### 6.2 Python 环境

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,metrics]"
```

DISTS 按原仓库说明单独安装。

## 7. 确切运行脚本

### 7.1 代码 smoke test

```bash
bash scripts/run_pilot_mock.sh
```

该命令不使用正式数据和模型，只验证 noise/blur、counterfactual lattice、rollout 和 coupling pipeline。

### 7.2 准备 DIV2K pilot split

假设 DIV2K validation 原图位于：

```text
/datasets/DIV2K/DIV2K_valid_HR
```

执行：

```bash
python tools/prepare_image_split.py \
  --input-dir /datasets/DIV2K/DIV2K_valid_HR \
  --output-dir data_sources/div2k_valid_first20 \
  --count 20 \
  --offset 0 \
  --mode symlink
```

### 7.3 Pilot InstructIR audit

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/pilot_noise_blur.yaml \
  data_sources/div2k_valid_first20 \
  instructir
```

### 7.4 DIV2K 正式主实验

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/formal_div2k_noise_blur.yaml \
  /datasets/DIV2K/DIV2K_valid_HR \
  instructir
```

### 7.5 Kodak24 OOD

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/ood_kodak24_noise_blur.yaml \
  /datasets/Kodak24 \
  instructir
```

## 8. 输出文件

每个实验写入各自 `output_root`：

```text
rollouts/
analysis/
├── directed_coupling.csv
├── directionality_summary.csv
├── directional_asymmetry.csv
├── state_dependence_report.csv
├── parameter_conditioned_summary.csv
└── matched_error_analysis.csv
```

所有正式结果必须保存当前：

```text
config
executor checkpoint
prompt file
git commit
raw degradation parameters
application order
```

## 9. Pilot 继续条件

Pilot 至少满足以下条件才运行 100 张正式实验：

1. 所有 480 programs 和 960 directed paths 完整；
2. coupling decomposition error `< 1e-7`；
3. 至少一个 direction 的 mean signed coupling 为正，且 bootstrap 95% CI 不完全落在 0 以下；
4. 两个 restoration orders 存在可测的 paired directional difference；
5. coupling 不完全由 `mid_error` 单调解释；
6. 随机抽查图像确认 denoise/deblur prompt 与输出语义正确。

若 3–5 不成立，不进入 interface learning；优先检查 action pair、退化匹配和 baseline 能力。
