# 贡献与提交规范

## 1. 分支

```text
main                 仅保存教师验收后的稳定版本
student-a/week1      学生 A：数据与 rollout
student-b/week1      学生 B：指标与标签
```

禁止直接 push 到 `main`。

## 2. 文件所有权

| 路径 | 主要负责人 |
|---|---|
| `lineA/` | 学生 A |
| `lineB/` | 学生 B |
| `shared/`、`configs/` | 教师 |
| `docs/` | 教师维护，学生通过 PR 建议修改 |
| `tests/` | A/B 均可修改，但必须说明覆盖的问题 |

学生不得直接修改对方目录。需要跨线修改时，在 PR 中明确说明接口原因。

## 3. 每日提交规划

### 学生 A

| 日期 | 最低 commit |
|---|---|
| Day 1 | `chore(lineA): add clean manifest and environment report` |
| Day 2 | `feat(lineA): add deterministic degradation generation` |
| Day 3 | `feat(lineA): add executor adapter and single-step rollout` |
| Day 4 | `feat(lineA): add ordered two-step rollout and integrity check` |
| Day 5 | `docs(lineA): add week1 results and known issues` |

### 学生 B

| 日期 | 最低 commit |
|---|---|
| Day 1 | `test(lineB): verify PSNR LPIPS and DISTS input protocol` |
| Day 2 | `feat(lineB): add unified quality evaluator` |
| Day 3 | `feat(lineB): add immediate-gain labels` |
| Day 4 | `feat(lineB): add directed-influence and identity validation` |
| Day 5 | `docs(lineB): add week1 label report and failure cases` |

commit 应小而可回滚。禁止将五天工作压成一个 `final update`。

## 4. Commit 类型

```text
feat      新功能
fix       修复错误
test      测试
docs      文档
refactor  不改变行为的代码整理
chore     环境或配置
```

格式：

```text
type(scope): imperative summary
```

示例：

```text
feat(lineA): add deterministic haze-rain generation
fix(lineB): convert LPIPS inputs to [-1,1]
test(shared): cover ordered action-pair naming
docs: record week1 Gate decision
```

## 5. Pull Request

PR 标题：

```text
[Line A][Week 1] Add deterministic data and rollout pipeline
[Line B][Week 1] Add metrics, labels and identity validation
```

PR 描述必须包含：

1. 本 PR 回答的唯一问题；
2. 修改范围；
3. 完整运行命令；
4. 输出路径；
5. 样本数量和当前数字；
6. 失败样本；
7. 测试结果；
8. 未解决问题。

教师使用 Squash Merge。Squash commit 使用 PR 标题。

## 6. 合并 Gate

Line A 合并条件：

- 20 个样本；
- 每个样本 3 个单步、6 个有序双步；
- float32 `[0,1]`；
- 相同 seed 可复现；
- integrity check 通过。

Line B 合并条件：

- 指标输入范围正确；
- gain/influence 无 NaN；
- identity 最大误差 `<1e-5`；
- 输出 per-sample CSV；
- 测试通过。

## 7. 提交前检查

```bash
pytest -q
python -m lineA.scripts.check_rollout_integrity \
  --config configs/week1_shared.yaml
```

不提交：

```text
data/
outputs/
checkpoint
模型权重
完整第三方仓库
终端截图
未脱敏本地路径
```
