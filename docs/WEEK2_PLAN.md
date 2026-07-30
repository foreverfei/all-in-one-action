# Week 2：Noise–Blur Directed Coupling Pilot

## 1. 本周问题

在 predecessor 单步误差相近时，`denoise -> deblur` 与
`deblur -> denoise` 是否仍产生不同的 directed coupling？这种差异会不会随图像、
退化强度或退化生成顺序变化？

本周目标是得到可信的 Pilot 证据，不预设结果必须为正。

## 2. 固定边界

正式设置以 `docs/EXPERIMENT_PROTOCOL.md` 和
`configs/pilot_noise_blur.yaml` 为准。当前只固定：

- DIV2K validation 前 20 张，中心裁剪 256×256；
- noise + motion blur，两个 degradation application orders；
- frozen InstructIR-7D，actions 为 `denoise` / `deblur`；
- 480 degradation programs、960 directed action paths；
- primary metric 为 Charbonnier distance；
- coupling 定义和 action/degradation mapping 不变；
- 本周不训练模型，也不实现 RL 或 planner。

旧 haze/rain/low-light 配置只用于工程 smoke test。

如需改变数据、actions、prompts、primary metric 或 coupling 定义，先提出理由，并使用
新的实验 ID；其他实现和分析选择由学生自行决定。

## 3. Line A

目标：生成可复现、可供 Line B 独立读取的 counterfactual states 和
actual/oracle rollouts。

最低证据：

- Pilot 覆盖率和失败情况；
- 参数、seed、application order、checkpoint 和 commit 可追溯；
- 抽样证明 counterfactual state 与 rollout 语义正确；
- 数据能够通过双方约定的文件或 metadata 接口交给 Line B。

Line A 可以自行决定数据组织、缓存方式、抽查策略、错误诊断和可视化形式。

分支：`student-a`

## 4. Line B

目标：判断 coupling 是否存在、是否具有方向性，以及这种现象能否由 mid error 单独解释。

最低证据：

- 可追溯到单条 path 的 coupling 结果；
- 两个 restoration directions 的比较；
- matched mid-error 或其他合理的控制分析；
- 不确定性、失败案例和负结果；
- non-commutativity 与 directed coupling 分开解释。

Line B 可以自行决定统计组织、分箱或匹配方法、辅助指标、图表和案例选择。若采用不同于
默认脚本的方法，需要说明理由和对结论的影响。

分支：`student-b`

## 5. 教师职责

- 确认正式协议、数据清单和 checkpoints；
- 在 Pilot 早期抽查少量样本的方向和语义；
- 处理需要改变正式实验边界的提议；
- 根据证据给出 `PASS / FAIL / REPEAT / STOP`。

教师关注结论是否可信，不要求学生采用指定的实现步骤或每日节奏。

## 6. 建议入口

仓库已有脚本可作为起点，但不是唯一允许的工作路线：

```bash
bash scripts/run_pilot_mock.sh configs/pilot_noise_blur.yaml

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

学生可以拆分、替换或扩展分析流程，只要不改变固定边界，并保留可复核证据。

## 7. Pilot Gate

### 数据与实现

- 结果覆盖范围明确，缺失和失败均有说明；
- 关键状态和方向可复现、可追溯；
- coupling 分解和 direction mapping 正确。

### 科学判断

结果需要回答：

1. coupling 是否存在；
2. 两个方向是否不同；
3. 控制 mid error 后差异是否仍在；
4. 现象对图像、强度或 application order 是否敏感。

允许结论为“没有足够证据”或负结果。Gate 根据证据质量判断，而不是根据是否得到预期
现象判断。

## 8. 协作

| 角色 | Issue | 分支 |
|---|---|---|
| Line A | [#7](https://github.com/foreverfei/all-in-one-action/issues/7) | `student-a` |
| Line B | [#8](https://github.com/foreverfei/all-in-one-action/issues/8) | `student-b` |
| 教师 | [#9](https://github.com/foreverfei/all-in-one-action/issues/9) | `main` |

进展在对应 Issue 中按里程碑更新，不要求每日填写固定模板。PR 只需说明修改、验证证据和
已知限制。

## 9. Pilot 之后

若证据支持继续，运行 DIV2K 100 张和 Kodak24；主要现象稳定后再制定 Week 3 方法计划。
若证据不足，则记录原因，选择补充实验、调整协议或停止该方向。
