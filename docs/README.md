# 项目文档索引

本目录保存项目协议、每周执行计划、学生协作规范和环境接入说明。

> 首页只保留项目概览和快速入口；每周的详细任务、Gate、命令和交付物统一写入独立的 `WEEK{N}_PLAN.md`。

---

## 1. 当前阶段

| 周次 | 阶段 | 核心问题 | 状态 | 文档 |
|---|---|---|---|---|
| Week 1 | P0 工程链路 | 数据、冻结执行器、单步/双步 rollout、gain/influence、identity 是否可靠 | 已建立 | [WEEK1_PLAN.md](WEEK1_PLAN.md) |
| Week 2 | P1 科学审计 | 反事实 subset state、actual/oracle path、directed coupling 是否成立 | 已建立 | [WEEK2_PLAN.md](WEEK2_PLAN.md) |
| Week 3 | P2 方法验证 | successor-conditioned interface learning 是否降低 coupling 且保持单步质量 | 待 P1 通过 | `WEEK3_PLAN.md`，通过 P1 后创建 |
| Week 4 | P3 泛化验证 | 未见退化组合、severity 和 backbone 泛化是否成立 | 待 P2 通过 | `WEEK4_PLAN.md`，通过 P2 后创建 |

阶段关系：

```text
Week 1：P0 工程链路与质量二阶差分
    ↓
Week 2：P1 反事实状态与定向 coupling 审计
    ↓
Week 3：P2 successor-conditioned interface learning
    ↓
Week 4：P3 未见组合与 backbone 泛化
```

**后续周次不得提前实现。只有上一阶段 Gate 通过后，教师才创建下一周文档、Issue 和学生分支。**

---

## 2. 核心文档入口

| 文档 | 用途 |
|---|---|
| [WEEK1_PLAN.md](WEEK1_PLAN.md) | Week 1 数据、rollout、指标与 identity 任务 |
| [WEEK2_PLAN.md](WEEK2_PLAN.md) | Week 2 counterfactual state 与 directed coupling audit |
| [WEEK_TEMPLATE.md](WEEK_TEMPLATE.md) | Week 3、Week 4 及后续计划的统一模板 |
| [STUDENT_WORKFLOW.md](STUDENT_WORKFLOW.md) | Issue 反馈、每日更新、阻塞上报和结果写作规范 |
| [INSTRUCTIR_SETUP.md](INSTRUCTIR_SETUP.md) | 官方 InstructIR 环境、checkpoint 和 adapter 接入 |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | 分支、commit、PR 和代码审查规范 |

---

## 3. 周次文档命名规范

```text
docs/WEEK1_PLAN.md
docs/WEEK2_PLAN.md
docs/WEEK3_PLAN.md
docs/WEEK4_PLAN.md
...
```

每份周计划必须包含：

```text
1. 本周定位与唯一科学问题
2. 与前一周的关系
3. 教师统一配置
4. Line A / Line B 分工
5. 新增与保留的代码
6. 输入、输出和数据 schema
7. 每日节点
8. 最低交付物
9. 自动测试
10. Gate 与 Stop conditions
11. 本周不做的内容
12. 下一周启动条件
```

禁止在首页堆叠完整周计划；首页只链接到本索引。

---

## 4. Issue、PR 与文档的职责

```text
Issue：任务、每日反馈、阻塞、实验数字、周末结论
PR：代码、配置、测试和文档变更
WEEK_PLAN：教师锁定的周任务与 Gate
result_summary.md：一次实验的完整结果记录
```

详细规则见 [STUDENT_WORKFLOW.md](STUDENT_WORKFLOW.md)。

---

## 5. 每周建立顺序

教师在新一周开始前按以下顺序操作：

```text
1. 上一周 Gate 给出 PASS
2. 复制 WEEK_TEMPLATE.md 为 WEEK{N}_PLAN.md
3. 锁定本周唯一问题、数据版本、指标和 Gate
4. 创建 Line A、Line B、Teacher 三个 Issue
5. 从最新 main 创建 student-a/week{N}、student-b/week{N}
6. 更新本索引与首页状态
7. 学生开始执行
```

若上一周为 `FAIL`、`REPEAT` 或 `STOP`，不得创建下一周方法代码。