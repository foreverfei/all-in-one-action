# All-in-One Action

面向 **All-in-One 图像复原动作影响（Action Influence）** 的可复现实验仓库。

本仓库第一阶段只建立可靠的实验基础设施：

```text
clean GT
  -> mixed degradation
  -> frozen All-in-One executor
  -> single-step / two-step rollout
  -> PSNR / LPIPS / DISTS
  -> immediate gain / directed influence
  -> two-step identity validation
```

> 第一周不训练网络，不运行 PPO/IQL，不修改 InstructIR 参数。

## 1. 研究问题

固定单一共享参数的 All-in-One restoration executor，研究：

1. 当前动作 `a` 是否改变后续动作 `b` 的边际恢复收益；
2. 这种影响是否依赖当前图像状态；
3. 低阶 action influence 是否能够提高未见退化组合下的动作排序与序列决策。

第一周使用三个动作：

```text
dehaze
derain
enhance
```

## 2. 团队分工

| 任务线 | 负责人 | 第一周目标 |
|---|---|---|
| Line A：Data & Rollout | 学生 A | 生成可复现双退化数据，接入 frozen InstructIR，保存单步和双步 Tensor |
| Line B：Metric & Label | 学生 B | 实现统一指标，生成 gain/influence 标签，验证 two-step identity |
| Protocol & Review | 教师 | 固定 action、prompt、指标协议、Gate 与合并标准 |

两条线只共享：

```text
configs/week1_shared.yaml
shared/metadata_schema.json
shared/action_prompts.yaml
sample_id / action name / tensor range / output schema
```

## 3. 仓库结构

```text
all-in-one-action/
├── configs/
│   └── week1_shared.yaml
├── shared/
│   ├── action_prompts.yaml
│   └── metadata_schema.json
├── lineA/
│   ├── degradations.py
│   ├── executors/
│   │   ├── base.py
│   │   └── instructir_wrapper.py
│   └── scripts/
│       ├── generate_week1_data.py
│       ├── generate_week1_rollouts.py
│       └── check_rollout_integrity.py
├── lineB/
│   ├── metrics/
│   │   └── quality_metrics.py
│   └── scripts/
│       ├── build_week1_labels.py
│       └── validate_identity.py
├── tests/
│   └── test_two_step_identity.py
├── docs/
│   ├── WEEK1_PLAN.md
│   └── STUDENT_WORKFLOW.md
├── pyproject.toml
└── CONTRIBUTING.md
```

运行时数据统一写入 `outputs/` 和 `data/`，两者均不提交 Git。

## 4. 快速开始

### 4.1 克隆与环境

```bash
git clone https://github.com/foreverfei/all-in-one-action.git
cd all-in-one-action
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

可选指标依赖：

```bash
pip install lpips
pip install git+https://github.com/dingkeyan93/DISTS.git
```

### 4.2 先运行 mock pipeline

mock executor 不需要模型权重，用于检查目录、命名、标签和 identity：

```bash
python -m lineA.scripts.generate_week1_data \
  --config configs/week1_shared.yaml \
  --mock-clean-count 4

python -m lineA.scripts.generate_week1_rollouts \
  --config configs/week1_shared.yaml \
  --executor mock

python -m lineA.scripts.check_rollout_integrity \
  --config configs/week1_shared.yaml

python -m lineB.scripts.build_week1_labels \
  --config configs/week1_shared.yaml \
  --metrics psnr

python -m lineB.scripts.validate_identity \
  --labels outputs/week1/labels/identity_check.csv

pytest -q
```

### 4.3 接入 InstructIR

1. 按官方仓库安装 InstructIR：`https://github.com/mv-lab/InstructIR`；
2. 不要复制 checkpoint 到本仓库；
3. 在本地配置中设置模型代码与 checkpoint 路径；
4. 完成 `lineA/executors/instructir_wrapper.py` 中标记的 adapter 接口；
5. 先用 1 张图执行 `dehaze`，确认 shape、dtype、range 后再批量运行。

## 5. 第一周固定协议

| 项目 | 值 |
|---|---|
| clean images | 20 |
| image size | 256 x 256 |
| tensor dtype | float32 |
| tensor range | [0, 1] |
| actions | dehaze / derain / enhance |
| ordered pairs | 6 |
| metrics | PSNR / LPIPS / DISTS |
| identity threshold | 1e-5 |

质量向量：

```text
m(x, gt) = [PSNR(x, gt), -LPIPS(x, gt), -DISTS(x, gt)]
```

Immediate gain：

```text
g_a(x) = m(T_a(x), gt) - m(x, gt)
```

Directed influence：

```text
eta_a_to_b(x)
  = m(T_b(T_a(x)), gt)
  - m(T_a(x), gt)
  - m(T_b(x), gt)
  + m(x, gt)
```

Two-step identity：

```text
m(T_b(T_a(x)), gt) - m(x, gt)
  = g_a(x) + g_b(x) + eta_a_to_b(x)
```

identity 是定义产生的恒等式。误差超过阈值表示数据、路径或指标实现错误，不能解释为更强 interaction。

## 6. 分支与提交规范

固定分支：

```text
main                 教师验收后的稳定版本
student-a/week1      Line A 第一周开发
student-b/week1      Line B 第一周开发
```

禁止直接向 `main` 提交。每名学生每天至少一个可回滚 commit，推荐格式：

```text
feat(lineA): add deterministic haze-rain generation
feat(lineA): add mock executor rollout cache
fix(lineA): keep rollout tensors in float32

feat(lineB): add unified PSNR interface
feat(lineB): build directed influence labels
fix(lineB): align LPIPS input range to [-1,1]

docs: update week1 progress and known issues
test: add two-step identity regression test
```

提交前必须执行：

```bash
pytest -q
python -m lineA.scripts.check_rollout_integrity --config configs/week1_shared.yaml
```

## 7. Pull Request 规则

学生 PR 必须包含：

```text
1. 本 PR 回答的唯一问题
2. 修改文件
3. 运行命令
4. 输出路径
5. 当前数字
6. 失败样本或已知问题
7. 自检结果
```

建议标题：

```text
[Line A][Week 1] Add deterministic data and rollout pipeline
[Line B][Week 1] Add metrics, labels and identity validation
```

教师审核后使用 **Squash and merge** 合并，保证 `main` 历史清晰。

## 8. 第一周 Gate

Line A：

- 20 张输入均有 3 个单步和 6 个有序双步输出；
- 相同 seed 输出一致；
- 正式指标读取 float32 Tensor，不读取预览 PNG；
- 所有输出可追溯到 sample、seed、config、action、checkpoint 和 commit。

Line B：

- PSNR 输入 `[0,1]`；
- LPIPS 输入 `[-1,1]`；
- DISTS 输入 `[0,1]`；
- gain/influence 无 NaN、无缺失；
- 最大 identity error `< 1e-5`。

两条线均通过后，第二周才进入 static action-pair matrix 与 state-conditioned dynamic influence 对比。

## 9. 文档入口

- 第一周任务：[`docs/WEEK1_PLAN.md`](docs/WEEK1_PLAN.md)
- 学生提交与协作：[`docs/STUDENT_WORKFLOW.md`](docs/STUDENT_WORKFLOW.md)
- 贡献规范：[`CONTRIBUTING.md`](CONTRIBUTING.md)

## 10. 外部参考

- InstructIR: https://github.com/mv-lab/InstructIR
- RL-Restore: https://github.com/yuke93/RL-Restore
- LPIPS: https://github.com/richzhang/PerceptualSimilarity
- DISTS: https://github.com/dingkeyan93/DISTS
- NAFNet: https://github.com/megvii-research/NAFNet
