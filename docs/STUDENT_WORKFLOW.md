# 学生协作与实验反馈手册

本项目使用 GitHub 管理任务、实验反馈、代码提交和教师验收。

核心规则：

```text
Issue：任务与实验反馈
Issue comment：每日进展、阻塞、当前数字、周末总结
PR：代码、配置、测试和文档合并
WEEK_PLAN：教师锁定的任务与 Gate
```

---

## 1. 每周只维护一个主 Issue

每名学生每周一个主 Issue，例如：

```text
[Line A][Week 2] Build counterfactual states and actual/oracle rollouts
[Line B][Week 2] Audit directed coupling and state dependence
```

教师在一周开始前创建并锁定：

- 本周唯一问题；
- 任务清单；
- 最低交付；
- Gate；
- 分支名称；
- PR 标题。

学生不得自行改变 Issue 中的核心任务定义。

### 不要每天新建 Issue

每日进展统一评论在当周主 Issue 下。

只有以下情况才单独创建新 Issue：

1. 当前阻塞会影响多名成员或主干；
2. 发现独立的软件缺陷，需要单独跟踪修复；
3. 教师明确要求拆成新的实验问题；
4. 后续周次正式启动。

---

## 2. 每日反馈格式

学生每天在当周主 Issue 下添加一条评论。

```markdown
## YYYY-MM-DD｜Line A 或 Line B｜姓名

### 今日计划
- [ ] 具体脚本：
- [ ] 具体命令：
- [ ] 预期输出：

### 实际完成
- [ ]

### 当前数字
- 数据版本：
- 样本或 program 数：
- 成功数：
- 失败数：
- 当前核心指标：
- executor calls：

### 产出路径
- 代码：
- 配置：
- 数据：
- CSV：
- 图表：
- 日志：

### 当前阻塞
- 现象：
- 完整错误：
- 已尝试：
- 是否需要教师决策：

### 当前 commit
- commit：

### 明日任务
- [ ]
```

禁止只写：

```text
继续调试
继续学习
跑实验
看代码
```

必须写清脚本、命令、数字、输出路径和错误。

---

## 3. 阻塞反馈

### 一般阻塞

直接评论在当周主 Issue 下，并 @ 教师。

必须提供：

```text
Exp ID
Git commit
数据版本
配置文件
完整命令
完整 traceback
预期行为
实际行为
已尝试修复
相关日志和文件路径
```

### 独立阻塞 Issue

当问题影响主干或两条任务线时，使用仓库的 Blocker Issue 模板单独建立 Issue。

标题格式：

```text
[Blocker][Week N][Line A] InstructIR output range exceeds [0,1]
[Bug][Shared] Week 2 metadata direction mapping is reversed
```

新建阻塞 Issue 后，必须在当周主 Issue 评论中链接该 Issue。

---

## 4. 实验结果反馈

### 中间结果

在当周主 Issue 评论中更新，必须包含：

- 当前配置；
- 样本数；
- per-sample CSV 路径；
- 核心指标；
- 失败样本；
- 是否达到当前检查点。

### 周末结果

学生在当周主 Issue 下提交最终评论：

```markdown
# Week N 最终结果｜Line A 或 Line B

## 1. 本周唯一问题

## 2. 实际完成

## 3. 未完成项

## 4. 关键产出
- 代码：
- 配置：
- 数据：
- CSV：
- 图表：
- 日志：

## 5. 主要数字

| 指标 | 数值 | Gate |
|---|---:|---|

## 6. 失败样本

## 7. 当前结论

## 8. 当前不能得出的结论

## 9. 建议决策

PASS / FAIL / REPEAT / STOP

## 10. 关联 PR
- #
```

教师在该评论后给出最终 Gate 决策。

---

## 5. PR 负责什么

PR 只用于合并：

```text
代码
配置
测试
文档
小规模结果摘要
```

不使用 PR 代替每日实验反馈。

PR 必须：

1. 从当周学生分支创建；
2. 链接当周主 Issue；
3. 包含运行命令；
4. 包含关键数字；
5. 说明失败样本和未完成项；
6. 通过 CI；
7. 教师审核后 Squash Merge。

PR 描述中加入：

```text
Closes #<当周主 Issue 编号>
```

若 PR 尚未完成，不要使用 `Closes`，改用：

```text
Related to #<Issue 编号>
```

---

## 6. 分支与 commit

分支：

```text
student-a/week1
student-b/week1
student-a/week2
student-b/week2
student-a/weekN
student-b/weekN
```

禁止直接提交到 `main`。

每天至少一个可回滚 commit。推荐：

```text
feat(lineA): generate formal counterfactual subset states
fix(lineA): preserve degradation seed after subset deletion
feat(lineB): build directed coupling table
fix(lineB): correct action direction mapping
analysis(lineB): add matched-error summary
 docs: add Week 2 failure cases
```

一个 commit 只解决一个明确问题。

---

## 7. 实验文件与 Git 的边界

允许提交：

```text
Python code
YAML/JSON schema
small fixture
unit test
CSV summary
Markdown report
small figures
```

禁止提交：

```text
模型权重
完整数据集
大规模 rollout Tensor
大量中间图片
环境缓存
完整 outputs/
```

大文件保存在服务器或共享存储，在 Issue 和报告中记录路径与校验信息。

---

## 8. result_summary.md

每个关键实验都需要本地或共享存储中的 `result_summary.md`。

```markdown
# Exp ID

## 1. 本实验回答什么问题

## 2. 假设

## 3. 固定设置
- data version：
- split：
- executor：
- checkpoint：
- actions：
- metrics：
- seeds：
- executor calls：

## 4. 比较方法

## 5. 主要结果

## 6. 统计证据

## 7. 失败样本

## 8. 结果判断
PASS / FAIL / REPEAT

## 9. 当前可以得出的结论

## 10. 当前不能得出的结论

## 11. 下一步
```

---

## 9. 科研结果写作

统一顺序：

```text
问题
→ 设置
→ 结果
→ 数值证据
→ 判断
→ 失败样本
→ 结论边界
```

推荐：

> 在 120 个 degradation programs 上，所有 counterfactual subset states 均可由 metadata 重渲染，最大像素误差低于预注册阈值，因此 P1-A 数据完整性检查通过。

禁止：

> 实验证明模型理解了退化之间的因果关系。

Week 1 identity 只验证标签实现；Week 2 coupling 只表示固定 executor 下的 predecessor-induced excess error。

---

## 10. 教师验收包

教师只接受以下完整结果包：

```text
config.yaml
command.txt
git_commit.txt
metrics.json
per_sample_results.csv
figures/
failure_cases/
result_summary.md
executor_call_ledger.csv
```

教师最终决策：

```text
PASS / FAIL / REPEAT / STOP
```

未获得 PASS 时，不得创建下一周方法分支。
