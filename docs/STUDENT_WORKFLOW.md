# 学生协作手册

## 1. 每日更新

```markdown
## YYYY-MM-DD｜Line A 或 Line B｜姓名

### 今日任务
- [ ]

### 实际完成
- [ ]

### 当前数字
- 样本数：
- 成功数：
- 失败数：
- 最大 identity error：

### 产出
- 代码：
- 配置：
- 数据：
- 图表：
- 日志：

### 当前阻塞
- 现象：
- 完整错误：
- 已尝试：
- 需要教师决定：

### 明日任务
- [ ]
```

禁止只写“继续调试”“继续学习”。

## 2. 问题上报

必须提供：

```text
Exp ID
git commit
data version
config
command
full traceback
expected behavior
actual behavior
attempted fixes
relevant paths
```

## 3. 周末报告

```markdown
# 第一周个人报告

## 本人负责的问题
## 完成内容
## 关键产出
## 主要数字
## 失败样本
## 当前问题
## 是否达到 P0
## 下周建议
```

## 4. 结果写作

按以下顺序：

```text
问题
-> 设置
-> 结果
-> 数值证据
-> 判断
-> 失败样本
-> 结论边界
```

推荐：

> 在 120 个有序 action-pair 样本上，最大 identity error 为 2.1e-13，低于预注册阈值 1e-5，因此标签生成链路通过 P0。

禁止：

> 实验证明模型理解了动作之间的因果关系。

第一周 identity 只验证代码正确，不验证科学假设。

## 5. 教师验收

教师只接受：

```text
config.yaml
command.txt
git_commit.txt
metrics.json
per_sample_results.csv
figures/
failure_cases/
result_summary.md
```

最终决策：

```text
PASS / FAIL / REPEAT / STOP
```
