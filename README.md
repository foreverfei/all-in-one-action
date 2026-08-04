# All-in-One Action

面向 All-in-One 图像复原中多步 action 组合问题的实验仓库。

## 1. 研究目标

当前研究不以 RL 选择顺序为起点，而是先判断：前序 restoration action 的输出误差是否会对后续 action 产生额外、具有方向性和状态依赖的影响。

对于 action path：

```text
source
  -> action_i
actual intermediate
  -> action_j
actual final
```

使用 counterfactual oracle intermediate 分解：

```text
mid_error
successor_intrinsic_error
actual_path_error
signed_coupling = actual_path_error - successor_intrinsic_error
harmful_coupling = max(signed_coupling, 0)
```

当前主问题：

> 在 predecessor 单步误差受控时，`denoise -> deblur` 与 `deblur -> denoise` 是否仍产生不同的 directed coupling？

---

## 2. 当前阶段

| 周次 / 阶段 | 固定任务 | 状态 |
|---|---|---|
| Week 1 | rollout、metrics、identity scaffold | 已建立 |
| Week 2 | counterfactual state、path 和 coupling 测量协议验证 | 当前需验收 |
| Week 3 | 真实 InstructIR action competence + DIV2K-20 Pilot | 计划已固定，待 Week 2 PASS |
| Formal audit | DIV2K-100 + Kodak24 / BSD100 | 待 Week 3 PASS |
| Method stage | 根据真实结果决定训练目标 | 未启动 |

关键边界：

```text
Week 2 PASS 只证明测量协议可信
Week 3 PASS 才证明当前现象值得进入正式实验或方法设计
```

当前禁止提前实现 planner、PPO、IQL、dynamics model 或 coupling-aware training。

---

## 3. 正式实验设置

### 数据集

| 用途 | 数据集 | 图像数 | 配置 |
|---|---|---:|---|
| Week 3 Pilot | DIV2K validation 前 20 张 | 20 | `configs/pilot_noise_blur.yaml` |
| Formal audit | DIV2K validation 全部 | 100 | `configs/formal_div2k_noise_blur.yaml` |
| OOD | Kodak24 | 24 | `configs/ood_kodak24_noise_blur.yaml` |

预处理为中心裁剪 256×256；短边不足时先等比例放大。指标不通过 PNG/JPEG 中间文件计算。

### 退化参数

```text
Gaussian noise: sigma = 15 / 25 / 50
Motion blur: length = 9 / 17
Motion blur angle = -30 / +30 degrees
Application order:
  noise -> motion_blur
  motion_blur -> noise
```

20-image Pilot：

```text
20 images × 3 noise × 4 blur × 2 application orders
= 480 degradation programs
= 960 directed action paths
```

### 主 baseline

```text
Method: InstructIR
Variant: official 7D checkpoint
State: frozen
Actions: denoise / deblur
Restoration orders:
  denoise -> deblur
  deblur -> denoise
Prompts: shared/action_prompts.yaml
```

当前正式模型只使用 frozen InstructIR-7D。Restormer denoiser/deblurrer experts 仅在真实 Pilot 通过后作为跨架构对照。

完整定义见 [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md)。

---

## 4. 执行入口

### 环境

```bash
git clone https://github.com/foreverfei/all-in-one-action.git
cd all-in-one-action
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,metrics]"
```

### Week 2：测量协议验证

```bash
bash scripts/run_pilot_mock.sh configs/pilot_noise_blur.yaml
```

该命令只用于验证：

```text
deterministic degradations
counterfactual states
actual/oracle path mapping
coupling computation
analysis script execution
unit tests
```

mock 结果不能作为科学证据。

### 准备 Week 3 DIV2K-20 split

```bash
python tools/prepare_image_split.py \
  --input-dir /datasets/DIV2K/DIV2K_valid_HR \
  --output-dir data_sources/div2k_valid_first20 \
  --count 20 \
  --offset 0 \
  --mode symlink
```

### Week 3：真实 InstructIR Pilot

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/pilot_noise_blur.yaml \
  data_sources/div2k_valid_first20 \
  instructir
```

执行完整 Pilot 前，先按照 [Week 3 计划](docs/WEEK3_PLAN.md) 完成独立 2-image mini-pilot 和教师抽查。

### Formal DIV2K audit

仅在 Week 3 PASS 后运行：

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

---

## 5. 输出

基础 coupling pipeline 在对应 `output_root/analysis/` 生成：

```text
directed_coupling.csv
directionality_summary.csv
directional_asymmetry.csv
state_dependence_report.csv
parameter_conditioned_summary.csv
matched_error_analysis.csv
order_baseline_summary.csv
```

Week 3 还需补齐：

```text
action_competence.csv
action_competence_summary.csv
mid_error_control.csv
secondary_metric_audit.csv
```

Primary metric 为 mean Charbonnier distance；PSNR、LPIPS、DISTS 和 non-commutativity 用于辅助复核。

---

## 6. 两条任务线

| 任务线 | 工作 |
|---|---|
| Line A | 数据、退化程序、counterfactual states、actual/oracle rollouts、完整性与追溯 |
| Line B | competence、coupling table、配对方向分析、cluster statistics、mid-error control |
| 教师 | 固定协议、语义抽查、代码审查、Gate 和论文判断 |

学生长期分支：

```text
student-a
student-b
```

每个阶段开始前先同步最新 `main`；进展、阻塞和结果优先记录在对应 Issue。

---

## 7. 文档入口

- [正式实验协议](docs/EXPERIMENT_PROTOCOL.md)
- [项目文档索引](docs/README.md)
- [Week 1：基础工程](docs/WEEK1_PLAN.md)
- [Week 2：测量协议验证](docs/WEEK2_PLAN.md)
- [Week 3：真实 competence 与 Pilot](docs/WEEK3_PLAN.md)
- [学生协作流程](docs/STUDENT_WORKFLOW.md)
- [InstructIR 接入](docs/INSTRUCTIR_SETUP.md)
- [贡献规范](CONTRIBUTING.md)

运行数据、模型权重和大规模输出写入 `data/`、`outputs/` 或外部存储，不提交 Git。
