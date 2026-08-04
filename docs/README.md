# 项目文档索引

本目录保存研究协议、每周计划、学生协作规范和环境接入说明。

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
Week 2 PASS
  = 测量协议、oracle 和 path mapping 可信

Week 3 PASS
  = action competence、coupling existence 和独立 direction/state effect 成立
```

不得使用 Week 2 mock 结果支持论文科学结论，也不得在 Week 3 Gate 前实现训练方法。

---

## 2. 核心文档

| 文档 | 用途 |
|---|---|
| [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | 跨阶段共享的数据、baseline、退化、metrics、统计协议和 Gate |
| [WEEK1_PLAN.md](WEEK1_PLAN.md) | 基础 rollout、metrics 和 identity scaffold |
| [WEEK2_PLAN.md](WEEK2_PLAN.md) | counterfactual measurement protocol validation |
| [WEEK3_PLAN.md](WEEK3_PLAN.md) | 真实 InstructIR competence、mini-pilot 和 DIV2K-20 Pilot |
| [WEEK_TEMPLATE.md](WEEK_TEMPLATE.md) | 后续周计划模板 |
| [STUDENT_WORKFLOW.md](STUDENT_WORKFLOW.md) | Issue、实验记录和结果提交规范 |
| [INSTRUCTIR_SETUP.md](INSTRUCTIR_SETUP.md) | 官方 InstructIR 环境、代码和 checkpoint 接入 |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | 分支、commit 和 PR 规范 |

旧 haze/rain/low-light 设置仅作为历史工程 smoke。当前论文主协议为 noise–motion blur，具体设置以 [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) 为准。

---

## 3. 当前任务入口

### Week 2

| 角色 | Issue | 分支 |
|---|---|---|
| 学生 A | [#7 Counterfactual states and actual/oracle rollouts](https://github.com/foreverfei/all-in-one-action/issues/7) | `student-a` |
| 学生 B | [#8 Directed coupling measurement and analysis](https://github.com/foreverfei/all-in-one-action/issues/8) | `student-b` |
| 教师 | [#9 Measurement protocol Gate](https://github.com/foreverfei/all-in-one-action/issues/9) | `main` |

Week 2 Issue 当前主要用于记录：

```text
mock protocol execution
oracle rerender validation
rollout direction checks
golden coupling fixtures
table and analysis invariants
PASS / REPEAT / STOP
```

### Week 3

Week 2 PASS 后创建：

```text
[Line A][Week 3] Run real InstructIR competence and coupling pilot
[Line B][Week 3] Audit competence and controlled directional coupling
[Teacher][Week 3] Action competence and scientific Gate
```

学生继续使用长期分支：

```text
student-a
student-b
```

---

## 4. 文档与协作职责

```text
EXPERIMENT_PROTOCOL
  固定跨阶段正式定义，不记录日常进度

WEEK_PLAN
  固定当周问题、边界、分工、交付和 Gate

Issue
  记录执行进度、阻塞、关键数字、结果路径和阶段结论

PR
  提交代码、配置、测试、文档和小型结果摘要

result_summary.md / Issue 总结
  记录一次正式实验回答了什么、证据是什么、结论边界在哪里
```

数据集、checkpoint、prompt、退化参数、action pair、primary metric 或 coupling 定义变化时：

```text
先更新 EXPERIMENT_PROTOCOL
-> 使用新的 experiment ID
-> 再更新周计划、配置和代码
```

---

## 5. 当前执行顺序

```text
1. 完成 Week 2 mock protocol validation
2. 教师给出 PASS / REPEAT / STOP
3. PASS 后创建 Week 3 Issues 和 mini-pilot config
4. 运行 2-image real InstructIR mini-pilot
5. 教师抽查 action 与 counterfactual 语义
6. 运行 DIV2K-20 full Pilot
7. 进行 clean_id-cluster statistics 和 mid-error control
8. 根据 Week 3 Gate 决定正式扩展、调整 claim 或停止
```
