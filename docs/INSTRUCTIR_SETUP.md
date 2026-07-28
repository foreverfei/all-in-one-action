# InstructIR 接入说明

本仓库不复制 InstructIR 源码和权重，通过 `lineA/executors/instructir_wrapper.py` 调用官方实现。

## 1. 准备官方仓库

```bash
mkdir -p external
git clone https://github.com/mv-lab/InstructIR.git external/InstructIR
```

按官方 README 安装依赖并准备：

```text
external/InstructIR/configs/eval5d.yml
external/InstructIR/models/im_instructir-7d.pt
external/InstructIR/models/lm_instructir-7d.pt
```

正式 noise-blur 配置默认使用以上路径。

## 2. 正式 action prompts

统一使用 `shared/action_prompts.yaml`：

```text
denoise: Remove Gaussian noise from the image while preserving image details.
deblur: Remove motion blur from the image while preserving image details.
```

不得在不同顺序或不同数据集上临时修改 prompt。若修改 prompt，必须建立新实验 ID 和新配置。

## 3. 本地路径

公共配置使用仓库相对路径。若本地路径不同，复制配置：

```bash
cp configs/pilot_noise_blur.yaml configs/local_pilot_noise_blur.yaml
```

修改：

```yaml
executor:
  external_repo: /absolute/path/to/InstructIR
  config_path: /absolute/path/to/InstructIR/configs/eval5d.yml
  image_checkpoint: /absolute/path/to/im_instructir-7d.pt
  lm_head_checkpoint: /absolute/path/to/lm_instructir-7d.pt
  device: cuda
```

`configs/local*.yaml` 不提交 Git。

## 4. Pilot 检查

先运行代码 smoke test：

```bash
bash scripts/run_pilot_mock.sh
```

再运行真实 InstructIR pilot：

```bash
bash scripts/run_noise_blur_audit.sh \
  configs/local_pilot_noise_blur.yaml \
  data_sources/div2k_valid_first20 \
  instructir
```

随机抽查至少 5 个 program，确认：

```text
input/output shape: 256 × 256 × 3
input/output dtype: float32
input/output range: [0,1]
denoise 输出主要降低噪声
deblur 输出主要处理模糊
无 PNG/JPEG 中间读写
```

## 5. Adapter 行为

adapter 使用官方推理组件：

```text
eval5d.yml
-> instructir.create_model(...)
-> image-model checkpoint
-> LanguageModel
-> LMHead
-> model(image, text_embedding)
```

本仓库额外保证：

- 模型只加载一次；
- action prompt embedding 在初始化时计算并缓存；
- 图像模型和 text embedding 位于同一 device；
- 推理使用 `torch.no_grad()`；
- 输出直接转换为 float32 NumPy；
- 不通过 uint8 文件交换中间结果；
- rollout metadata 记录 checkpoint 和 baseline 配置。

## 6. 常见错误

### Missing InstructIR repository

检查 `executor.external_repo`。

### Missing InstructIR config/checkpoint

检查 `config_path`、`image_checkpoint` 和 `lm_head_checkpoint` 是否为真实文件。

### Checkpoint key mismatch

确认 `eval5d.yml`、image checkpoint 和 LM-head checkpoint 属于同一官方版本。

### CUDA device mismatch

先将 `device` 设置为 `cpu` 定位加载问题，不在 wrapper 中临时移动部分层。

### Hugging Face model 无法下载

`LanguageModel` 会加载 InstructIR 配置中指定的文本模型。需要提前下载或配置本地缓存。
