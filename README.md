# All-in-One Action

面向 **All-in-One 图像复原动作影响与定向耦合** 的可复现实验仓库。

本项目固定单一共享参数的 All-in-One restoration executor，研究：

1. 前序 restoration action 是否改变后续 action 的边际恢复能力；
2. 这种影响是否依赖当前图像状态、退化强度和退化组合；
3. 低阶 counterfactual evidence 是否能够支持后续 interface learning 与组合泛化。

> 项目按周次和 Gate 推进。不得在前一阶段未通过时提前实现下一阶段方法。

---

## 1. 当前项目路线

```text
Week 1：P0 工程链路与质量二阶差分
    ↓
Week 2：P1 反事实状态与定向 coupling 审计
    ↓
Week 3：P2 successor-conditioned interface learning
    ↓
Week 4：P3 未见组合与 backbone 泛化
```

| 周次 | 核心任务 | 状态 | 入口 |
|---|---|---|---|
| Week 1 | frozen rollout、PSNR/LPIPS/DISTS、gain/influence、identity | 已建立 | [执行计划](docs/WEEK1_PLAN.md) |
| Week 2 | subset states、actual/oracle path、directed coupling | 已建立 | [执行计划](docs/WEEK2_PLAN.md) |
| Week 3 | interface learning | 待 Week 2 P1 Gate | 通过后创建 `docs/WEEK3_PLAN.md` |
| Week 4 | composition/backbone generalization | 待 Week 3 P2 Gate | 通过后创建 `docs/WEEK4_PLAN.md` |

完整文档索引见：**[docs/README.md](docs/README.md)**。

---

## 2. 两套定义禁止混用

### Week 1：quality interaction diagnostics

```text
m(x, gt) = [PSNR(x, gt), -LPIPS(x, gt), -DISTS(x, gt)]

g_a(x) = m(T_a(x), gt) - m(x, gt)

eta_a_to_b(x)
  = m(T_b(T_a(x)), gt)
  - m(T_a(x), gt)
  - m(T_b(x), gt)
  + m(x, gt)
```

用途：验证单步/双步质量变化和标签 pipeline。

### Week 2：predecessor-induced excess error

```text
mid_error
  = d(actual_mid, oracle_mid)

successor_intrinsic_error
  = d(oracle_successor, final_target)

actual_path_error
  = d(actual_final, final_target)

signed_coupling
  = actual_path_error - successor_intrinsic_error

harmful_coupling
  = max(signed_coupling, 0)
```

用途：分离 predecessor error 对 successor 的额外影响。

`non_commutativity` 单独报告，不等同于 directed coupling。

---

## 3. 团队分工

| 任务线 | 负责人 | 主要职责 |
|---|---|---|
| Line A：Data & Rollout | 学生 A | controlled states、degradation program、executor、actual/oracle rollout、integrity |
| Line B：Metric & Analysis | 学生 B | metrics、labels、coupling table、directionality、state dependence、统计图表 |
| Protocol & Review | 教师 | 周计划、配置、Gate、Issue、代码审查、科学结论 |

两条线只通过固定文件接口和 metadata schema 协作，不直接依赖对方内部实现。

---

## 4. 学生如何反馈实验

### Issue：任务和反馈主入口

每名学生每周只维护一个主 Issue，例如：

```text
[Line A][Week 2] Build counterfactual states and actual/oracle rollouts
[Line B][Week 2] Audit directed coupling and state dependence
```

该 Issue 用于：

```text
任务清单
每日进展评论
当前数字
阻塞和完整错误日志
失败样本
周末结果总结
教师 PASS / FAIL / REPEAT / STOP
```

**不要每天新建 Issue。**每日反馈统一评论在当周主 Issue 下。

### PR：代码合并入口

PR 只用于：

```text
代码
配置
测试
文档
小规模可提交结果摘要
```

PR 必须关联当周 Issue：

```text
Closes #7
```

详细规范见：

- [学生协作手册](docs/STUDENT_WORKFLOW.md)
- [贡献规范](CONTRIBUTING.md)
- [PR 模板](.github/pull_request_template.md)

---

## 5. 分支规范

```text
main                 教师验收后的稳定版本
student-a/week1      学生 A Week 1
student-b/week1      学生 B Week 1
student-a/week2      学生 A Week 2
student-b/week2      学生 B Week 2
student-a/weekN      后续周次统一命名
student-b/weekN
```

禁止直接向 `main` 提交。

教师审核后使用 **Squash and merge**，使每个合并提交对应一个完整阶段交付。

---

## 6. 仓库结构

```text
all-in-one-action/
├── configs/
│   ├── week1_shared.yaml
│   └── week2_shared.yaml
├── shared/
│   ├── action_prompts.yaml
│   ├── metadata_schema.json
│   └── week2_metadata_schema.json
├── lineA/
│   ├── degradations.py
│   ├── degradation_program.py
│   ├── lattice_renderer.py
│   ├── executors/
│   └── scripts/
│       ├── generate_week1_data.py
│       ├── generate_week1_rollouts.py
│       ├── check_rollout_integrity.py
│       ├── generate_week2_states.py
│       ├── generate_week2_rollouts.py
│       └── check_week2_integrity.py
├── lineB/
│   ├── metrics/
│   ├── coupling/
│   └── scripts/
│       ├── build_week1_labels.py
│       ├── validate_identity.py
│       ├── build_week2_coupling_table.py
│       ├── analyze_directionality.py
│       └── analyze_state_dependence.py
├── tests/
├── docs/
│   ├── README.md
│   ├── WEEK1_PLAN.md
│   ├── WEEK2_PLAN.md
│   ├── WEEK_TEMPLATE.md
│   ├── STUDENT_WORKFLOW.md
│   └── INSTRUCTIR_SETUP.md
├── .github/
├── CONTRIBUTING.md
└── pyproject.toml
```

运行数据、模型权重和大规模输出写入 `data/`、`outputs/` 或外部存储，均不提交 Git。

---

## 7. 环境安装

```bash
git clone https://github.com/foreverfei/all-in-one-action.git
cd all-in-one-action

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

可选指标：

```bash
pip install lpips
pip install git+https://github.com/dingkeyan93/DISTS.git
```

真实 InstructIR 接入见：**[docs/INSTRUCTIR_SETUP.md](docs/INSTRUCTIR_SETUP.md)**。

---

## 8. Week 1 mock pipeline

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
```

Week 1 Gate：

```text
3 single actions per sample
6 ordered pairs per sample
all arrays float32 RGB [0,1]
max identity error < 1e-5
```

---

## 9. Week 2 mock pipeline

```bash
python -m lineA.scripts.generate_week2_states \
  --config configs/week2_shared.yaml \
  --mock-clean-count 2

python -m lineA.scripts.generate_week2_rollouts \
  --config configs/week2_shared.yaml \
  --executor mock

python -m lineA.scripts.check_week2_integrity \
  --config configs/week2_shared.yaml

python -m lineB.scripts.build_week2_coupling_table \
  --config configs/week2_shared.yaml

python -m lineB.scripts.analyze_directionality \
  --config configs/week2_shared.yaml

python -m lineB.scripts.analyze_state_dependence \
  --config configs/week2_shared.yaml
```

Week 2 Gate：

```text
counterfactual subset states are reproducible
actual/oracle path semantics are correct
coupling decomposition error < 1e-7
non-commutativity reported separately
```

运行全部测试：

```bash
pytest -q
```

GitHub Actions 会自动运行 Week 1 和 Week 2 mock pipeline。

---

## 10. 文档入口

| 文档 | 入口 |
|---|---|
| 项目文档总索引 | [docs/README.md](docs/README.md) |
| Week 1 执行计划 | [docs/WEEK1_PLAN.md](docs/WEEK1_PLAN.md) |
| Week 2 执行计划 | [docs/WEEK2_PLAN.md](docs/WEEK2_PLAN.md) |
| 后续周次模板 | [docs/WEEK_TEMPLATE.md](docs/WEEK_TEMPLATE.md) |
| 学生实验反馈规范 | [docs/STUDENT_WORKFLOW.md](docs/STUDENT_WORKFLOW.md) |
| InstructIR 接入 | [docs/INSTRUCTIR_SETUP.md](docs/INSTRUCTIR_SETUP.md) |
| 分支与提交规范 | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## 11. 外部参考

- InstructIR: https://github.com/mv-lab/InstructIR
- RL-Restore: https://github.com/yuke93/RL-Restore
- LPIPS: https://github.com/richzhang/PerceptualSimilarity
- DISTS: https://github.com/dingkeyan93/DISTS
- NAFNet: https://github.com/megvii-research/NAFNet
