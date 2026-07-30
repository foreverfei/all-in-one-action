# All-in-One Action

面向 All-in-One 图像复原中多步 action 组合问题的实验仓库。

## 1. 研究目标

当前研究不以 RL 选顺序为主，而是分析并降低前序 restoration action 对后续 action 造成的额外误差。

对于 action path：

```text
source x_S
  -> action_i
actual intermediate
  -> action_j
actual final
```

使用反事实中间状态分解：

```text
mid_error
successor_intrinsic_error
actual_path_error
signed_coupling = actual_path_error - successor_intrinsic_error
harmful_coupling = max(signed_coupling, 0)
```

当前主问题是：在 predecessor 单步误差相近时，`denoise -> deblur` 和 `deblur -> denoise` 是否仍产生不同的 directed coupling。

## 2. 当前正式实验

### 数据集

| 实验 | 数据集 | 图像数 | 配置 |
|---|---|---:|---|
| Pilot | DIV2K validation 前 20 张 | 20 | `configs/pilot_noise_blur.yaml` |
| 主实验 | DIV2K validation 全部 | 100 | `configs/formal_div2k_noise_blur.yaml` |
| OOD | Kodak24 | 24 | `configs/ood_kodak24_noise_blur.yaml` |

预处理统一为中心裁剪 256×256，不通过 PNG 中间文件计算指标。

### 退化

```text
Gaussian noise: sigma = 15 / 25 / 50
Motion blur: length = 9 / 17
Motion blur angle = -30 / +30 degrees
Application order:
  noise -> motion_blur
  motion_blur -> noise
```

Pilot 共生成：

```text
20 images × 3 noise × 4 blur × 2 orders
= 480 degradation programs
= 960 directed action paths
```

### 主 baseline

```text
Method: InstructIR
Variant: official 7D checkpoint
State: frozen
Actions: denoise / deblur
Orders:
  denoise -> deblur
  deblur -> denoise
```

固定 prompt 位于 `shared/action_prompts.yaml`。

后续方法消融：

| 方法 | 训练目标 |
|---|---|
| Frozen InstructIR | 不训练 |
| Mid-only | oracle intermediate supervision |
| Mid+Path | intermediate + two-step path loss |
| Ours | intermediate + excess coupling + successor interface loss |

当前 Pilot 的正式模型只使用 frozen InstructIR-7D。Restormer 的官方彩色高斯去噪和运动去模糊专家可在
Pilot 后作为分离模型链对照；PromptIR 和 OneRestore 的官方权重不覆盖当前 noise–motion blur
组合，不纳入本轮实验。

完整协议见 [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md)。

## 3. 快速开始

### 环境

```bash
git clone https://github.com/foreverfei/all-in-one-action.git
cd all-in-one-action
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,metrics]"
```

### 代码 smoke test

```bash
bash scripts/run_pilot_mock.sh
```

### 准备 DIV2K pilot split

```bash
python tools/prepare_image_split.py \
  --input-dir /datasets/DIV2K/DIV2K_valid_HR \
  --output-dir data_sources/div2k_valid_first20 \
  --count 20 \
  --offset 0 \
  --mode symlink
```

### Pilot InstructIR audit

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/pilot_noise_blur.yaml \
  data_sources/div2k_valid_first20 \
  instructir
```

### 正式 DIV2K audit

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/formal_div2k_noise_blur.yaml \
  /datasets/DIV2K/DIV2K_valid_HR \
  instructir
```

### Kodak24 OOD

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/ood_kodak24_noise_blur.yaml \
  /datasets/Kodak24 \
  instructir
```

InstructIR 安装和 checkpoint 路径见 [docs/INSTRUCTIR_SETUP.md](docs/INSTRUCTIR_SETUP.md)。

## 4. 输出

每个实验在对应 `output_root/analysis/` 生成：

```text
directed_coupling.csv
directionality_summary.csv
directional_asymmetry.csv
state_dependence_report.csv
parameter_conditioned_summary.csv
matched_error_analysis.csv
```

Primary metric 为 mean Charbonnier distance；PSNR、LPIPS、DISTS 和 non-commutativity 作为辅助指标。

## 5. 阶段实验

| 阶段 | 目标 | 继续条件 |
|---|---|---|
| 工程验证 | 数据、rollout、指标实现正确 | 自动测试通过 |
| Pilot coupling audit | 20 张 DIV2K 验证 coupling 是否存在 | 存在正向 coupling、方向差异且不完全由 mid error 解释 |
| 正式 coupling audit | DIV2K 100 张 + Kodak24 | 主要结论跨内容和强度稳定 |
| Interface learning | 降低 harmful coupling | 单步质量基本不下降，coupling 显著降低 |
| 泛化验证 | 未见强度、数据集、组合和 backbone | 结论不依赖单一设置 |

当前优先完成 Pilot，不提前实现 planner、PPO、IQL 或 dynamics model。

## 6. 分工

| 任务线 | 工作 |
|---|---|
| Line A | 数据、退化程序、counterfactual states、actual/oracle rollouts |
| Line B | coupling table、方向性、强度分析、matched-error analysis |
| 教师 | 固定协议、代码审查、结果验收和论文判断 |

## 7. 文档

- [正式实验协议](docs/EXPERIMENT_PROTOCOL.md)
- [项目文档索引](docs/README.md)
- [Week 1 计划](docs/WEEK1_PLAN.md)
- [Week 2 计划](docs/WEEK2_PLAN.md)
- [学生协作流程](docs/STUDENT_WORKFLOW.md)
- [InstructIR 接入](docs/INSTRUCTIR_SETUP.md)
- [贡献规范](CONTRIBUTING.md)

运行数据、模型权重和大规模输出写入 `data/`、`outputs/` 或外部存储，不提交 Git。
