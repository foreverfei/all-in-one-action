# 第一周执行计划

## 总目标

建立两条互不等待的实验线：

```text
Line A：controlled data -> frozen executor -> rollout cache
Line B：metric -> gain/influence -> exact identity
```

第一周不训练模型，不做 RL。

## Line A

最低交付：

- 20 张 clean images；
- 20 张 mixed-degradation inputs；
- 每张图 3 个单步输出；
- 每张图 6 个有序双步输出；
- 完整 metadata；
- integrity check；
- 3 组恢复链可视化；
- `student_A_week1.md`。

## Line B

最低交付：

- PSNR / LPIPS / DISTS 统一接口；
- `gain_labels.csv`；
- `influence_labels.csv`；
- `identity_check.csv`；
- 最大 identity error `<1e-5`；
- 正负 influence 各 3 个例子；
- `student_B_week1.md`。

## 每日节点

| 日期 | Line A | Line B |
|---|---|---|
| Day 1 | manifest、InstructIR demo | 指标安装和单元测试 |
| Day 2 | degradation config、executor adapter | metrics API、gain |
| Day 3 | 5 个样本的完整 rollout | influence、identity |
| Day 4 | 20 个正式 rollout | 读取正式数据生成 CSV |
| Day 5 | 完整性报告、可视化 | 统计、失败样本、Gate 报告 |

## 联调接口

Line A 输出：

```text
sample_id/
  input.npy
  dehaze.npy
  derain.npy
  enhance.npy
  dehaze__derain.npy
  ...
  metadata.json
```

Line B 只通过该接口读取数据，不依赖 Line A 内部实现。

## Gate

只有同时满足以下条件才进入第二周：

- Line A integrity check 全部通过；
- Line B identity 最大误差 `<1e-5`；
- A/B 均能独立运行 mock pipeline；
- 所有输出可追溯到 config 和 commit。
