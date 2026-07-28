# Week N 执行计划：阶段名称

> 用途：教师锁定本周问题、学生任务、代码边界、交付物和 Gate。  
> 前置条件：仅在 Week N-1 Gate 为 PASS 时创建。  
> 原则：本周只回答一个核心问题，不提前实现下一阶段。

---

## 1. 本周定位

### 与前一周的关系

```text
Week N-1 已完成：

Week N 新增：
```

### 本周唯一科学问题

> 

### 本周不做

```text
不做内容 1
不做内容 2
不做内容 3
```

---

## 2. 教师统一配置

```text
数据版本：
Executor / checkpoint：
Actions：
训练或评估 split：
Primary metric：
Secondary metrics：
Random seeds：
输出根目录：
Gate threshold：
```

学生不得自行修改上述内容。

---

## 3. 团队分工

| 任务线 | 负责人 | 本周唯一问题 |
|---|---|---|
| Line A | 学生 A |  |
| Line B | 学生 B |  |
| Protocol & Review | 教师 |  |

两条线仅通过固定文件接口和 metadata schema 协作。

---

# 4. Line A

## 4.1 保留代码

```text
```

## 4.2 新增代码

```text
```

## 4.3 输入

```text
```

## 4.4 输出

```text
```

## 4.5 最低交付

```text
```

## 4.6 完成标准

- [ ] 
- [ ] 
- [ ] 

---

# 5. Line B

## 5.1 保留代码

```text
```

## 5.2 新增代码

```text
```

## 5.3 输入

```text
```

## 5.4 输出

```text
```

## 5.5 最低交付

```text
```

## 5.6 完成标准

- [ ] 
- [ ] 
- [ ] 

---

# 6. 每日节点

| 日期 | Line A | Line B | 教师检查 |
|---|---|---|---|
| Day 1 |  |  |  |
| Day 2 |  |  |  |
| Day 3 |  |  |  |
| Day 4 |  |  |  |
| Day 5 |  |  |  |

---

# 7. 自动测试

新增：

```text
tests/test_*.py
```

必须验证：

- [ ] 数据或状态语义；
- [ ] action direction / file mapping；
- [ ] 核心公式或 loss decomposition；
- [ ] shape、dtype、range；
- [ ] mock pipeline 可运行。

---

# 8. 本周 Gate

## Gate A：工程正确

- [ ] 

## Gate B：定义正确

- [ ] 

## Gate C：科学现象成立

- [ ] 

教师最终决策：

```text
PASS / FAIL / REPEAT / STOP
```

---

# 9. 下一周启动条件

只有满足以下条件，才创建 `WEEK{N+1}_PLAN.md`：

```text
```

---

# 10. Issue 与 PR

本周创建：

```text
[Line A][Week N] ...
[Line B][Week N] ...
[Teacher][Week N] ...
```

学生分支：

```text
student-a/weekN
student-b/weekN
```

PR 标题：

```text
[Line A][Week N] ...
[Line B][Week N] ...
```
