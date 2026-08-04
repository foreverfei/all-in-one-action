# Week N：简短标题

## 1. 本周定位

明确本周在研究链路中的位置，以及上一阶段的启动条件。

必须写清：

```text
本周回答什么问题
本周不回答什么问题
本周 PASS 后允许进入什么阶段
```

不要把实现步骤直接写成科学问题。

---

## 2. 固定代码、模型与数据设置

### 代码与配置

```text
Config:
关键脚本：
Repository commit / branch：
Seed：
Tensor shape / dtype / range：
```

### 模型

```text
Baseline：
Checkpoint：
Prompt / action：
Frozen / trainable：
```

### 数据

| 用途 | 数据集 / split | 样本数 | 预处理 | 是否用于科学结论 |
|---|---|---:|---|---|
| Smoke |  |  |  | 否 |
| Pilot |  |  |  |  |

### Primary / Secondary metrics

```text
Primary metric：
Secondary metrics：
统计单位：
随机种子 / bootstrap 设置：
```

若数据、checkpoint、prompt、action pair、primary metric 或核心定义变化，必须先更新 `EXPERIMENT_PROTOCOL.md` 并使用新的 experiment ID。

---

## 3. 实验清单

| 实验 ID | 实验名称 | 负责人 | 目的 |
|---|---|---|---|
| WN-E1 |  | Line A |  |
| WN-E2 |  | Line B |  |

每个实验只回答一个可判断问题。不要将数据生成、方法训练、统计分析和泛化验证混在同一个实验 ID 中。

---

## 4. 单个实验写法

对每个实验使用以下固定结构。

### WN-EX：实验名称

#### 目的 / 假设

写清实验要排除或支持的假设。

#### 基本代码设置

```text
执行脚本：
配置文件：
关键参数：
需要新增或修改的代码：
```

#### 参与数据

```text
数据集 / split：
clean image 数量：
program / path / pair 数量：
有效样本定义：
排除条件：
```

#### 输出

```text
输出文件：
逐样本字段：
日志与失败记录：
```

#### 分析方法

必须写清：

```text
主要变量
统计单位
比较组 / paired key
置信区间或显著性方法
需要检查的失败案例
```

#### 允许得出的结论

明确写成条件判断：

```text
若 A 成立：允许结论……
若 A 不成立：不允许结论……
```

禁止从工程 smoke、mock executor 或 post-hoc 可视化直接建立科学 claim。

#### 实验 Gate

```text
PASS：
FAIL：
REPEAT：
STOP：
```

---

## 5. Line A 与 Line B 分工

### Line A：`student-a`

```text
负责的实验 ID：
最低代码交付：
最低数据交付：
最低报告交付：
```

### Line B：`student-b`

```text
负责的实验 ID：
最低代码交付：
最低分析交付：
最低报告交付：
```

两条线通过固定 Tensor、CSV 和 metadata 接口协作，不依赖对方内部实现。

---

## 6. 本周结果总结格式

每个实验必须记录：

```text
实验 ID：
目的 / 假设：
代码 / config / commit：
模型 / checkpoint：
参与数据和有效样本数：
实际输出：
主要变量：
统计单位和分析方法：
关键数字与置信区间：
失败、缺失和不确定性：
允许得出的结论：
建议 Gate：PASS / FAIL / REPEAT / STOP
```

不得只报告总体均值，不得只提交截图而不提供逐样本结果路径。

---

## 7. 教师验收

教师只检查：

1. 实验是否使用冻结的正式设置；
2. 数据、代码、模型和结果是否可追溯；
3. 分析单位、配对关系和统计方法是否正确；
4. 证据是否足以支持所写结论；
5. 失败和不确定性是否被保留；
6. 是否满足进入下一阶段的条件。

---

## 8. Week Gate

列出进入下一阶段必须通过的实验 ID：

```text
Required PASS:
  WN-E1
  WN-E2
  ...
```

最终决策：

```text
PASS：本周核心问题得到足够证据，进入下一阶段。
FAIL：核心假设不成立，调整研究主张或方法路线。
REPEAT：工程、覆盖、统计或证据不足，重复当前阶段。
STOP：基础能力或现象不存在，停止当前 baseline/action pair。
```

---

## 9. 协作入口

| 角色 | Issue | 分支 |
|---|---|---|
| Line A |  | `student-a` |
| Line B |  | `student-b` |
| 教师 |  | `main` |

学生在对应 Issue 中按实验 ID 更新进展、结果路径、commit、阻塞和建议 Gate。
