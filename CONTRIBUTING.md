# 贡献与协作规范

本仓库按研究问题和 Gate 推进。规则只保证协作安全和结果可复核，不限定学生的探索路线。

## 1. 分支

仓库长期保留：

```text
main
student-a
student-b
```

- `main` 保存教师验收后的稳定版本；
- `student-a`、`student-b` 是两名学生的长期分支；
- 不按周创建新分支，也不直接向 `main` 提交；
- 新阶段开始前，将学生分支同步到最新 `main`。

## 2. Issue 与任务

每周或每阶段为每条任务线维护一个主 Issue。任务描述只需要：

- 一个清晰问题；
- 少量固定边界；
- 最低证据；
- Gate。

不要把教师偏好的实现步骤写成强制清单。学生可以自由选择代码结构、分析方法、辅助实验、
可视化和工作节奏，也可以提出新的假设。

## 3. 代码范围

| 路径 | 主要负责人 |
|---|---|
| `lineA/` | 学生 A |
| `lineB/` | 学生 B |
| `shared/`、`configs/` | 共同接口，修改时说明影响 |
| `docs/`、`tests/` | 共同维护 |
| `.github/` | 教师维护 |

跨任务线修改是允许的，只需在 PR 中解释原因，避免无意破坏另一条线的接口。

## 4. Commit 与 PR

建议使用清楚、可回滚的 commit，例如：

```text
feat(lineA): generate paired counterfactual states
analysis(lineB): compare coupling under matched mid error
fix(shared): preserve degradation seed
docs: summarize pilot findings
```

PR 需要包含：

- 关联 Issue；
- 修改内容和理由；
- 验证证据或结果路径；
- 已知限制、失败或未解决问题。

不要求固定数量的 commits、固定日报或统一的分析文件结构。

## 5. Gate

教师主要判断：

- 结果是否可复现、可追溯；
- 核心定义和方向是否正确；
- 证据是否回答研究问题；
- 不确定性和负结果是否被如实说明。

最终决策：`PASS / FAIL / REPEAT / STOP`。

## 6. 不提交的内容

```text
数据集
模型权重
完整 outputs/
大规模 rollout tensors
环境缓存
密钥或账号信息
```

大文件保存在服务器或共享存储，并在 Issue 或结果摘要中记录位置和必要的版本信息。
