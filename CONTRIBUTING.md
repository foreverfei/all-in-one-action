# 贡献、分支与提交规范

本仓库按周次和 Gate 推进。学生不直接向 `main` 提交，所有代码变更必须关联当周主 Issue。

---

## 1. Issue、分支与 PR 的关系

```text
WEEK_PLAN
  -> 教师创建当周主 Issue
  -> 从最新 main 创建 student-x/weekN
  -> 学生在 Issue 评论中反馈实验
  -> 学生提交 PR
  -> CI + 教师审查
  -> Squash Merge
  -> 教师在 Issue 中给出 Gate
```

职责：

```text
Issue：任务、每日反馈、阻塞、数字和周末结论
Branch：个人当周开发
PR：代码、配置、测试和文档合并
main：教师验收后的稳定版本
```

---

## 2. 分支命名

```text
main
student-a/week1
student-b/week1
student-a/week2
student-b/week2
student-a/weekN
student-b/weekN
```

禁止：

```text
dev
student-test
final
new-version
week2-final
```

新周分支必须从最新 `main` 创建。上一周 Gate 未通过时，不创建下一周方法分支。

---

## 3. 文件所有权

| 路径 | 主要负责人 |
|---|---|
| `lineA/` | 学生 A |
| `lineB/` | 学生 B |
| `shared/`、`configs/` | 教师锁定，学生通过 PR 修改 |
| `docs/` | 教师维护，学生可通过 PR 补充结果 |
| `tests/` | A/B 均可修改，但必须说明覆盖的问题 |
| `.github/` | 教师维护 |

学生不得无说明修改另一任务线目录。跨线修改必须在 Issue 和 PR 中说明接口原因。

---

## 4. Commit 规范

格式：

```text
type(scope): imperative summary
```

类型：

```text
feat      新功能
fix       修复错误
test      测试
docs      文档
analysis  分析脚本或统计输出
refactor  不改变行为的整理
chore     环境、配置或维护
```

示例：

```text
feat(lineA): generate formal counterfactual subset states
fix(lineA): preserve degradation seed after subset deletion
feat(lineB): build directed coupling table
analysis(lineB): add matched-error summary
test(shared): cover ordered action direction mapping
docs: record Week 2 P1 Gate decision
```

要求：

- 一个 commit 只解决一个明确问题；
- commit 必须可回滚；
- 不允许五天工作压成一个 `final update`；
- 不提交自动生成的大规模结果。

---

## 5. 每日提交建议

每名学生每天至少一个有意义的 commit。具体内容以当周 Issue 为准。

通用节奏：

| 日期 | 建议内容 |
|---|---|
| Day 1 | schema、配置或基础 API |
| Day 2 | 小规模数据或 golden fixture |
| Day 3 | 核心正式 pipeline |
| Day 4 | 完整实验、错误修复和统计 |
| Day 5 | 测试、失败案例和周报告 |

---

## 6. Pull Request

PR 标题：

```text
[Line A][Week N] Short deliverable description
[Line B][Week N] Short deliverable description
[Shared][Week N] Shared interface or protocol change
```

PR 必须关联当周主 Issue：

```text
Closes #<weekly_issue_number>
```

若 PR 不是最终交付：

```text
Related to #<weekly_issue_number>
```

PR 描述必须包含：

1. 周次与任务线；
2. 关联 Issue；
3. 本 PR 回答的唯一问题；
4. 修改范围；
5. 完整运行命令；
6. 数据、配置和 checkpoint；
7. 输出路径；
8. 样本数、核心数字和 executor calls；
9. 失败样本；
10. 测试结果；
11. 当前不能得出的结论。

使用仓库 PR 模板，不删除必填部分。

---

## 7. 合并 Gate

PR 合并前必须满足：

### 通用工程 Gate

- [ ] `pytest -q` 通过；
- [ ] 当周 mock pipeline 通过；
- [ ] shape、dtype、range 正确；
- [ ] 文件命名和 direction mapping 正确；
- [ ] 无 NaN、Inf 和未解释缺失；
- [ ] 输出可追溯到数据版本、配置和 commit。

### 实验 Gate

- [ ] 满足当周 `docs/WEEK{N}_PLAN.md`；
- [ ] per-sample CSV 已生成；
- [ ] 失败样本已保留；
- [ ] 总 executor-call 数已记录；
- [ ] 教师确认实验定义未被自行修改。

教师采用 **Squash and merge**。Squash commit 使用 PR 标题。

---

## 8. 提交前检查

通用：

```bash
pytest -q
```

Week 1：

```bash
python -m lineA.scripts.check_rollout_integrity \
  --config configs/week1_shared.yaml
```

Week 2：

```bash
python -m lineA.scripts.check_week2_integrity \
  --config configs/week2_shared.yaml

python -m lineB.scripts.build_week2_coupling_table \
  --config configs/week2_shared.yaml
```

后续周次命令写入对应 `WEEK{N}_PLAN.md`。

---

## 9. 禁止提交

```text
data/
outputs/
模型权重
checkpoint
完整第三方仓库
大量 rollout Tensor
环境缓存
终端截图
未脱敏本地路径
API key 或账号信息
```

允许提交小型 fixture、CSV 摘要和必要的示例图。

---

## 10. 教师审查重点

教师主要检查：

```text
是否回答当周唯一问题
是否关联正确 Issue
是否匹配数据与 executor-call budget
是否存在数据泄漏
是否保留失败样本
是否过度解释结果
是否满足当前 Gate
```

未通过审查时，教师在 PR 或主 Issue 中给出：

```text
FAIL / REPEAT / STOP
```

只有 `PASS` 后才创建下一周计划和分支。
