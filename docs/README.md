# 项目文档索引

本目录保存研究说明、正式实验协议、每周计划、学生协作规范和环境接入说明。

## 1. 当前研究阶段

| 阶段 | 任务 | 状态 | 文档 |
|---|---|---|---|
| 工程验证 | frozen rollout、质量指标和数据完整性 | 已建立 | [WEEK1_PLAN.md](WEEK1_PLAN.md) |
| 科学审计 | 反事实状态、actual/oracle path、directed coupling | 当前重点 | [WEEK2_PLAN.md](WEEK2_PLAN.md) |
| 方法训练 | successor-conditioned interface learning | 待科学审计通过 | 后续创建 |
| 泛化验证 | 未见强度、数据集、组合和 backbone | 待方法训练完成 | 后续创建 |

当前论文主实验不再使用 64×64 haze/rain/low-light smoke 设置。正式设置见：

- **[EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md)**：数据集、baseline、noise-blur 参数、样本规模和确切命令；
- **[INSTRUCTIR_SETUP.md](INSTRUCTIR_SETUP.md)**：InstructIR 环境与 checkpoint；
- **[WEEK2_PLAN.md](WEEK2_PLAN.md)**：现阶段学生分工和交付物。

## 2. 当前任务入口

| 角色 | Issue | 分支 |
|---|---|---|
| 学生 A | [#7 Counterfactual states and actual/oracle rollouts](https://github.com/foreverfei/all-in-one-action/issues/7) | `student-a` |
| 学生 B | [#8 Directed coupling and state-dependence audit](https://github.com/foreverfei/all-in-one-action/issues/8) | `student-b` |
| 教师 | [#9 Protocol and scientific review](https://github.com/foreverfei/all-in-one-action/issues/9) | `main` |

有重要结果、方向变化或阻塞时，在对应主 Issue 下更新。

## 3. 文档入口

| 文档 | 用途 |
|---|---|
| [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | 正式数据集、baseline、退化参数和运行脚本 |
| [WEEK1_PLAN.md](WEEK1_PLAN.md) | 工程 smoke test |
| [WEEK2_PLAN.md](WEEK2_PLAN.md) | directed coupling 审计任务 |
| [WEEK_TEMPLATE.md](WEEK_TEMPLATE.md) | 后续周计划模板 |
| [STUDENT_WORKFLOW.md](STUDENT_WORKFLOW.md) | Issue、实验记录和结果提交 |
| [INSTRUCTIR_SETUP.md](INSTRUCTIR_SETUP.md) | 官方 InstructIR 接入 |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | 分支、commit 和 PR 规范 |

## 4. 文档职责

```text
EXPERIMENT_PROTOCOL：固定数据集、baseline、参数和命令
WEEK_PLAN：说明本周问题、固定边界、分工和 Gate
Issue：记录任务进展、阻塞和当前数字
PR：提交代码、配置、测试和文档
result_summary.md：记录一次正式实验的结果与结论范围
```

数据集、checkpoint、退化参数或 primary metric 的变化必须先修改正式实验协议，再修改周计划和代码配置。
