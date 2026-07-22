# InstructIR 接入说明

本仓库不复制 InstructIR 源码和权重。统一通过 `lineA/executors/instructir_wrapper.py` 接入本地官方仓库。

## 1. 准备官方仓库

```bash
mkdir -p external
git clone https://github.com/mv-lab/InstructIR.git external/InstructIR
```

按照官方 README 安装依赖和下载权重。

Week 1 配置默认期望：

```text
external/InstructIR/configs/eval5d.yml
external/InstructIR/models/im_instructir-7d.pt
external/InstructIR/models/lm_instructir-7d.pt
```

如果路径不同，只修改本地配置文件，不修改学生公共代码。

## 2. 配置

复制公共配置：

```bash
cp configs/week1_shared.yaml configs/local_week1.yaml
```

修改：

```yaml
executor:
  external_repo: /absolute/path/to/InstructIR
  config_file: /absolute/path/to/InstructIR/configs/eval5d.yml
  image_checkpoint: /absolute/path/to/im_instructir-7d.pt
  lm_head_checkpoint: /absolute/path/to/lm_instructir-7d.pt
  device: auto
```

`configs/local*.yaml` 已加入 `.gitignore`，不得提交绝对本地路径。

## 3. 单图检查

先生成一张 mock 输入，再改用真实 executor：

```bash
python -m lineA.scripts.generate_week1_data \
  --config configs/local_week1.yaml \
  --mock-clean-count 1

python -m lineA.scripts.generate_week1_rollouts \
  --config configs/local_week1.yaml \
  --executor instructir
```

必须检查：

```text
shape: H x W x 3
dtype: float32
range: [0,1]
RGB order unchanged
no JPEG/uint8 round trip
```

## 4. 官方推理路径对应关系

adapter 与官方 `predict.py` 保持相同组件：

```text
eval5d.yml
  -> instructir.create_model(...)
  -> load image-model state dict
  -> LanguageModel
  -> LMHead
  -> text embedding
  -> model(image, text_embedding)
  -> clip output to [0,1]
```

本仓库的额外约束：

- 模型只加载一次；
- 图像模型放在指定 device；
- language model 和 LM head 在 CPU 生成 embedding；
- text embedding 再移动到图像模型 device；
- 输出直接转为 float32 NumPy；
- 不保存临时 PNG 后再读取。

## 5. 常见错误

### `Missing InstructIR repository`

检查 `external_repo` 是否存在。

### `Could not import models.instructir`

确认配置指向官方仓库根目录，而不是 `models/` 子目录。

### checkpoint key mismatch

确认使用的 config 与 checkpoint 属于同一官方版本。

### CUDA device mismatch

将 `device` 暂时设置为 `cpu` 定位问题；不要在 wrapper 内临时移动部分层。

### Hugging Face model 无法下载

`LanguageModel` 会加载配置中指定的文本模型。需要提前下载或配置可访问的本地缓存。
