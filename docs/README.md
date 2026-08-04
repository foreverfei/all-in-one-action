# 项目文档索引

本目录保存研究协议、每周实验计划、学生协作规范和环境接入说明。

## 1. 当前研究链路

| 阶段 | 固定任务 | 状态 | 文档 |
|---|---|---|---|
| Week 1 | rollout、metrics、identity scaffold | 已建立 | [WEEK1_PLAN.md](WEEK1_PLAN.md) |
| Week 2 | counterfactual state、path 和 coupling 测量协议验证 | 当前需验收 | [WEEK2_PLAN.md](WEEK2_PLAN.md) |
| Week 3 | 真实 InstructIR competence + DIV2K-20 scientific Pilot | 已固定，待 Week 2 PASS | [WEEK3_PLAN.md](WEEK3_PLAN.md) |
| Formal audit | DIV2K-100 + Kodak24 / BSD100 | 待 Week 3 PASS | [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) |
| Method stage | 根据真实结果选择训练目标 | 未启动 | Week 3 PASS 后创建 |
| Generalization | unseen severity / pair / backbone | 未启动 | 方法有效后创建 |

阶段解释：

```text
Week 1 PASS
  = 基础数据、rollout、metric 和 label 接口正确

Week 2 PASS
  = counterfactual oracle、path mapping 和 coupling 测量可信

Week 3 PASS
  = action competence、coupling existence 和独立 direction/state effect 成立
```

不得使用 Week 1/2 的 mock 结果支持论文科学结论，也不得在 Week 3 Gate 前实现训练方法。

---

## 2. 每周计划必须包含的内容

从当前版本开始，每个 `WEEKN_PLAN.md` 必须明确：

1. **本周定位**：上一阶段启动条件、本周问题和禁止提前开展的方向；
2. **固定代码设置**：config、脚本、seed、Tensor 协议、模型和 checkpoint；
3. **参与数据**：数据集、split、图像数、program/path 数量和排除条件；
4. **实验清单**：使用 `WN-EX` 编号，每个实验只回答一个问题；
5. **实验目的或假设**：说明要支持或排除的判断；
6. **实验输出**：逐样本 CSV、metadata、日志、失败记录和可视化；
7. **分析方法**：主要变量、统计单位、paired key、置信区间和失败案例；
8. **允许得出的结论**：明确哪些结果支持什么结论，哪些结论不允许建立；
9. **实验 Gate 与 Week Gate**：`PASS / FAIL / REPEAT / STOP`；
10. **结果总结格式**：代码、数据、数字、CI、失败和结论边界可追溯。

后续计划统一使用 [WEEK_TEMPLATE.md](WEEK_TEMPLATE.md)。

---

## 3. 当前每周实验结构

### Week 1

```text
W1-E1 deterministic degradation generation
W1-E2 single/two-step rollout integrity
W1-E3 metric input contract
W1-E4 gain/influence label construction
W1-E5 exact two-step identity
W1-E6 A/B interface integration
```

允许结论：基础工程接口正确；不允许建立真实 action interaction claim。

### Week 2

```text
W2-E1 noise–blur parameter-grid determinism
W2-E2 counterfactual oracle re-render
W2-E3 directed rollout mapping fixture
W2-E4 directed coupling golden fixture
W2-E5 coupling table integrity
W2-E6 paired/statistical script fixture
W2-E7 A/B independent reproduction
```

允许结论：测量协议可信；不允许声称真实模型存在 directed coupling。

### Week 3

```text
W3-E1 real-model mini-pilot integrity
W3-E2 action competence audit
W3-E3 DIV2K-20 full rollout audit
W3-E4 coupling existence test
W3-E5 paired direction effect
W3-E6 mid-error controlled effect
W3-E7 secondary metric robustness
W3-E8 severity/content failure audit
```

允许结论由 Gate 决定：进入正式扩展、调整为普通误差传播、重复实验或停止当前 action pair。

---

## 4. 核心文档

| 文档 | 用途 |
|---|---|
| [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | 跨阶段共享的数据、baseline、退化、metrics、统计协议和 Gate |
| [WEEK1_PLAN.md](WEEK1_PLAN.md) | 基础 rollout、metrics 和 identity 实验 |
| [WEEK2_PLAN.md](WEEK2_PLAN.md) | counterfactual measurement protocol validation |
| [WEEK3_PLAN.md](WEEK3_PLAN.md) | 真实 InstructIR competence、mini-pilot 和 DIV2K-20 Pilot |
| [WEEK_TEMPLATE.md](WEEK_TEMPLATE.md) | 后续周计划标准模板 |
| [STUDENT_WORKFLOW.md](STUDENT_WORKFLOW.md) | Issue、实验记录和结果提交规范 |
| [INSTRUCTIR_SETUP.md](INSTRUCTIR_SETUP.md) | 官方 InstructIR 环境、代码和 checkpoint 接入 |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | 分支、commit 和 PR 规范 |

当前论文主协议为 noise–motion blur。旧 haze/rain/low-light 设置仅作为历史工程 smoke。

---

## 5. 当前任务入口

### Week 2

| 角色 | Issue | 分支 |
|---|---|---|
| 学生 A | [#7 Counterfactual states and actual/oracle rollouts](https://github.com/foreverfei/all-in-one-action/issues/7) | `student-a` |
| 学生 B | [#8 Directed coupling measurement and analysis](https://github.com/foreverfei/all-in-one-action/issues/8) | `student-b` |
| 教师 | [#9 Measurement protocol Gate](https://github.com/foreverfei/all-in-one-action/issues/9) | `main` |

Week 3 Issue 只在 Week 2 `PASS` 后创建。

---

## 6. 结果记录与提交

每个实验在 Issue 或结果文档中至少记录：

```text
实验 ID
目的 / 假设
代码 / config / commit
模型 / checkpoint
参与数据和有效样本数
实际输出路径
主要变量和分析方法
关键数字与置信区间
失败、缺失和不确定性
允许得出的结论
建议 Gate
```

PR 只提交代码、配置、测试、文档和小型结果摘要。数据集、模型权重和完整大规模 outputs 不提交 Git。

---

## 7. 文档更新顺序

当数据、checkpoint、prompt、action pair、primary metric 或核心定义变化时，按以下顺序更新：

```text
EXPERIMENT_PROTOCOL.md
  -> 对应 WEEKN_PLAN.md
  -> config / code / tests
  -> Issue
  -> result summary
```

禁止只修改代码或 Issue 而不更新正式协议和周计划。
