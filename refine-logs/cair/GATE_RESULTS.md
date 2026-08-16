# CAIR Gate Results

> Status: ACTIVE SKELETON
>
> Primary utility: PSNR gain (dB)
>
> Statistical unit: `clean_id`
>
> Mandatory training repetitions: 3 seeds

本文件是 CAIR 的唯一 Gate 结果账本。`docs/CAIR_PROPOSAL.md` 定义方法和假设；本文件只记录实验输入、关键数字、置信区间、失败与 `PASS / FAIL / REPEAT / STOP` 决策。

---

## 1. Gate 总览

| Gate | 核心问题 | 当前状态 | 允许进入下一阶段的条件 |
|---|---|---:|---|
| G0 | executor、STOP、metric 和 split 是否可靠 | PENDING | 重复性、identity、追溯与数据隔离全部通过 |
| G1 | counterfactual lattice 与代数闭包是否正确 | PENDING | gain/influence/Q2 identity 在数值容差内成立 |
| G2 | 状态相关、有向 influence 是否真实存在 | PENDING | 超过噪声且优于 static/action-only 解释 |
| G3 | \(\hat g,\hat I\) 是否可学习并泛化 | PENDING | held-out image 上 ranking/sign/calibration 达标 |
| G4 | influence prior 是否改善 value estimation | PENDING | Full CAIR 稳定超过 B2–B7 关键控制 |
| G5 | selective action 是否产生非平凡策略收益 | PENDING | 超过 Always-STOP、predictor-only 和匹配覆盖控制 |
| G6 | horizon 2–6 与 OOD 上是否形成序列策略 | PENDING | 多 horizon 同号、OOD 不失效、三 seed 稳定 |

状态说明：

```text
PENDING  尚未运行正式实验
PASS     所有硬条件满足
FAIL     核心假设未满足，但允许按预注册修复项重复
REPEAT   工程/统计错误使结果无效，修复后原样重跑
STOP     科学假设或方法 admission 失败，终止当前主张
```

---

## 2. 30-state POC 回填

### 2.1 设置

```text
Executor: InstructIR CDD-11, frozen
Evaluation states: 30
Source validation images: 7
Seeds: 未形成正式 3-seed protocol
Statistical unit: state-level summary；未完成 clean-image cluster inference
Primary reported metric: PSNR gain (dB)
```

### 2.2 已知结果

| Policy | Mean Gain (dB) | Std | STOP% |
|---|---:|---:|---:|
| Random | -1.49 | 8.09 | 70.0 |
| Greedy | -3.26 | 11.51 | 3.3 |
| Direct IQL | -0.47 | 5.53 | 43.3 |
| Static ResIQL | -5.09 | 12.90 | 0.0 |
| Dynamic ResIQL | +0.48 | 1.84 | 93.3 |

派生比较：

```text
Dynamic ResIQL - Direct IQL = +0.95 dB
Dynamic ResIQL - Static ResIQL = +5.57 dB
Dynamic ResIQL - Random = +1.97 dB
```

若 STOP 是严格 identity 且无 step cost，则 Always-STOP 的解析参考值为 `0 dB`，Dynamic ResIQL 相对该参考仅为 `+0.48 dB`。该参考尚未作为正式 baseline 独立运行和统计。

### 2.3 POC 判定

```text
Decision: UNADMITTED / SELECTIVE-ACTION SIGNAL ONLY
```

原因：

1. 93.3% STOP 对应约 2/30 个状态执行非 STOP 动作；均值可能由极少数状态贡献。
2. 未运行 Always-STOP、predictor-only、matched-coverage 和 shuffled-prior 控制。
3. 未完成 3 seeds。
4. 30 states 由 7 images 派生，不能视为 30 个 IID 单位。
5. 未报告 clean-image paired effect、cluster bootstrap CI、beneficial recall 或 risk–coverage curve。
6. 当前 Dynamic ResIQL 的 prior 是否包含完整 directed influence 尚未由 gain-only 与 pair/state shuffle 对照隔离。

因此该 POC 不对应任何正式 Gate 的 PASS，仅用于决定继续执行 G0–G5。

---

## 3. 固定 baseline B0–B7

| ID | 方法 | 结构 | 主要排除的替代解释 | 适用 Gate |
|---|---|---|---|---|
| B0 | Always-STOP | 所有状态直接停止 | CAIR 是否只是保守停止 | G5–G6 |
| B1 | Predictor-only selective | 仅用完整 \(P_{CF}\)，validation 校准 STOP，不训练 residual critic | Residual IQL 是否必要 | G4–G6 |
| B2 | Direct IQL | 标准 state-action value learning | influence prior 是否优于直接 Q 学习 | G4–G6 |
| B3 | Parameter-matched Direct IQL | 扩宽 B2，使参数量与 CAIR 匹配 | 收益是否来自容量 | G4–G6 |
| B4 | Predictor-feature-concat IQL | 将 \(\hat g,\hat I\) 作为 feature 输入，但不执行 additive prior 分解 | 收益是否仅来自额外特征 | G4–G6 |
| B5 | Gain-only Residual IQL | \(P(s,a)=\hat g_s(a)+\max_b\hat g_s(b)\)，移除 \(\hat I\) | directed influence 是否必要 | G4–G6 |
| B6 | State-shuffled Influence ResIQL | 使用 \(\hat I_{\pi(s)}(a\to b)\) | state–influence 对齐是否必要 | G4–G6 |
| B7 | Pair-shuffled Influence ResIQL | 使用 \(\hat I_s(\rho(a,b))\) | 有序动作对语义是否必要 | G4–G6 |

Full CAIR 不编号为 baseline：

\[
Q_\theta(s,a)=\operatorname{sg}[P_{CF}(s,a)]+\Delta Q_\theta(s,a).
\]

额外上界只用于分析，不参与 admission：

```text
U1 Oracle-gain prior
U2 Oracle-gain + oracle-influence prior
U3 Oracle horizon-H action value
```

G2/G3 还必须包含以下 predictor-level controls：

```text
C1 global mean
C2 static ordered-pair table
C3 action-only predictor
C4 state-only predictor without action-pair conditioning
C5 K² independent-head predictor
```

---

## 4. G0 — Executor and Metric Reliability

### 4.1 问题

冻结 executor 的输出、STOP identity、PSNR 计算和数据 split 是否足以支撑低幅 gain/influence 测量？

### 4.2 固定实验

```text
G0-E1 repeated executor inference: 5 repeats/state/action
G0-E2 STOP identity and no-call audit
G0-E3 metric implementation cross-check
G0-E4 state/action/successor ID traceability
G0-E5 clean-image split leakage audit
G0-E6 cache consistency and checkpoint/config hash audit
```

### 4.3 输出

| 字段 | 结果 |
|---|---|
| Executor/checkpoint/config hash | TODO |
| Repeated states | TODO |
| Maximum PSNR repeat range | TODO |
| \(\sigma_{repeat}\) | TODO |
| STOP max absolute pixel error | TODO |
| Duplicate/leaked clean IDs | TODO |
| Missing transitions | TODO |

定义测量噪声阈值：

\[
\epsilon_M=\max(3\sigma_{repeat},10^{-4}\ \mathrm{dB}).
\]

### 4.4 PASS 条件

- 相同输入、动作、checkpoint 和 config 的 PSNR repeat range 不超过 \(\epsilon_M\)。
- STOP 通过直接返回当前状态实现，不调用 restoration executor，pixel-wise 完全相同。
- 所有 state、action、successor、clean reference、trajectory 可双向追溯。
- train/val/test 在 `clean_id` 级无交叉。
- cache key 包含 checkpoint、prompt/action ID、input hash 和 preprocessing hash。

```text
Status: PENDING
Decision evidence: TODO
```

---

## 5. G1 — Counterfactual Closure

### 5.1 问题

Oracle gain、directed influence 与二步 Q 分解是否由真实 rollout 一致地产生？

### 5.2 固定 identity

\[
I_s(a\to b)=g_{F(s,a)}(b)-g_s(b)
\]

\[
g_s(a)+g_s(b)+I_s(a\to b)
=M(F(F(s,a),b),x^*)-M(s,x^*)
\]

\[
Q_2^*(s,a)=g_s(a)+\max_b[g_s(b)+I_s(a\to b)].
\]

### 5.3 固定实验

```text
G1-E1 one-step branch completeness
G1-E2 ordered two-step branch completeness
G1-E3 gain/influence algebraic identity
G1-E4 Q2 direct-return equivalence
G1-E5 action-order and state-ID audit
G1-E6 independent implementation reproduction
```

### 5.4 PASS 条件

- 有效状态的全部 feasible one-step branches 完整。
- 预注册动作子集的全部 ordered two-step branches 完整。
- 上述两个 identity 的绝对误差均不超过 \(\epsilon_M\)。
- A/B 两套实现对随机抽取样本给出一致结果。
- 不允许使用未来 test labels 构造 predictor 输入。

```text
Status: PENDING
Valid states: TODO
Missing/invalid branches: TODO
Maximum closure error: TODO
Decision evidence: TODO
```

---

## 6. G2 — Influence Existence

### 6.1 假设 H1

冻结 executor 上存在超过测量噪声、具有方向性且随状态变化的 marginal utility shift：

\[
I_s(a\to b)\neq 0,
\quad
I_s(a\to b)\neq I_s(b\to a).
\]

### 6.2 固定分析

```text
G2-E1 off-diagonal |I| distribution vs epsilon_M
G2-E2 ordered direction asymmetry
G2-E3 within-pair sign reversal across states
G2-E4 between-image and within-image variance decomposition
G2-E5 static pair table vs state-conditioned predictor
G2-E6 action-only / state-shuffle controls
```

### 6.3 主要指标

| 指标 | 结果 |
|---|---|
| \(P(|I|>\epsilon_M)\) | TODO |
| Median / mean \(|I|\) | TODO |
| Direction asymmetry effect | TODO |
| Sign reversal rate | TODO |
| Static pair-table MAE | TODO |
| State-conditioned MAE | TODO |
| Image-cluster bootstrap CI | TODO |

### 6.4 PASS 条件

必须同时满足：

1. 至少一个预注册 ordered pair 在不少于 25% 的 held-out clean images 上满足 \(|I|>\epsilon_M\)。
2. 至少一个 pair 的 direction asymmetry 在 clean-image cluster bootstrap 95% CI 下不包含 0。
3. 至少一个 pair 在不少于 10% 的 held-out clean images 上发生超过 \(\epsilon_M\) 的 sign reversal。
4. state-conditioned predictor 相对 static ordered-pair table 的 held-out MAE 至少下降 5%，且 paired cluster-bootstrap CI 支持该改善。

若只有固定 pair 均值而无状态增益，则：

```text
Status: STOP
Reason: state-conditioned influence claim rejected
```

当前结果：

```text
Status: PENDING
Decision evidence: TODO
```

---

## 7. G3 — Influence Predictability and Generalization

### 7.1 假设 H2-a

仅根据当前 state image 与 action IDs，可预测 \(\hat g_s(a)\)、\(\hat I_s(a\to b)\) 以及解析二步价值排序。

### 7.2 数据边界

```text
Train/val/test split unit: clean_id
No clean reference in model input
No oracle successor in model input
No test-time counterfactual branching
```

### 7.3 主要指标

```text
gain MAE / sign macro-F1 / AUPRC
influence MAE / sign macro-F1 / calibration
Q2 pairwise ranking accuracy / Kendall tau
top-1 action accuracy
unseen severity, unseen ordered-pair, pair-to-triple transfer
```

### 7.4 PASS 条件

- Full shared ordered-pair predictor 相对 C2 static pair table：influence MAE 至少下降 5%。
- Q2 pairwise ranking accuracy 相对 gain-only predictor 至少提高 3 percentage points。
- 三个训练 seed 改善方向一致。
- ID held-out clean images 上的 cluster-bootstrap 95% CI 支持 ranking 改善。
- unseen severity 结果不得低于 ID gain-only baseline。

Unseen-pair 和 pair-to-triple 失败不会自动终止核心 ID claim，但必须移除相应 compositional-generalization 表述。

```text
Status: PENDING
ID results: TODO
OOD results: TODO
Decision evidence: TODO
```

---

## 8. G4 — Value Estimation

### 8.1 假设 H2-b

将 predicted directed influence 写入解析 prior，比直接 Q 学习、容量增加、feature concatenation、gain-only prior 和错误对齐 prior 更准确地估计 action value。

### 8.2 目标

```text
Primary short-horizon target: exact Q2 return
Secondary long-horizon target: held-out Monte Carlo return, H=3–6
```

### 8.3 指标

| 指标 | CAIR | B1 | B2 | B3 | B4 | B5 | B6 | B7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Q2 MAE | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| Pairwise ranking accuracy | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| Top-1 action accuracy | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| Q overestimation | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| ECE / Brier | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |

### 8.4 PASS 条件

- CAIR 相对 B3、B4、B5、B6、B7 的 Q2 MAE 更低，且三个 seed 方向一致。
- CAIR 相对 B5 的 pairwise ranking accuracy 至少提高 2 percentage points。
- CAIR 相对 B6 和 B7 的 pooled clean-image cluster-bootstrap 95% CI 下界大于 0。
- B6/B7 若与 Full CAIR 等价，则 directed/state-conditioned novelty 不成立，转为 `STOP`。

```text
Status: PENDING
Strongest validation control: TODO
Decision evidence: TODO
```

---

## 9. G5 — Selective Action Policy

### 9.1 假设 H3-a

在 held-out states 上，CAIR 能识别足够多的有益动作，而不是依靠接近 Always-STOP 的 coverage 获得低风险。

### 9.2 固定定义

定义 horizon-2 oracle opportunity：

\[
O(s)=\mathbb 1\left[\max_{a\neq STOP}Q_2^*(s,a)>\epsilon_M\right].
\]

定义：

\[
\mathrm{Coverage}=P(a\neq STOP),
\]

\[
\mathrm{OpportunityRecall}=P(a\neq STOP\mid O(s)=1),
\]

\[
\mathrm{BeneficialPrecision}=P(Q_2^*(s,a)>\epsilon_M\mid a\neq STOP).
\]

STOP threshold 只在 validation set 上校准。Matched-coverage 比较要求两个策略 coverage 差不超过 2 percentage points；否则使用同一 coverage 网格上的插值结果。

### 9.3 必须报告

```text
mean/median final PSNR gain
harmful-action rate
coverage
opportunity rate and opportunity recall
beneficial precision
risk–coverage curve
return–coverage curve
area under risk–coverage curve
per-image paired effect and cluster bootstrap CI
LPIPS/DISTS secondary audit
```

### 9.4 PASS 条件

1. 相对 B0、B1、B3、B4、B5、B6、B7，三个 seed 的 clean-image paired mean final gain 均为正。
2. 相对 validation 选出的 strongest learned control，pooled clean-image cluster-bootstrap 95% CI 下界大于 0。
3. matched coverage 下仍优于 B1、B3 和 B5。
4. OpportunityRecall 不低于 strongest learned control，且至少覆盖 50% 的 oracle opportunity states。
5. BeneficialPrecision 高于 B1 与 B3；harmful-action rate 不高于 strongest learned control。
6. LPIPS/DISTS 不出现跨三个 seed 一致的反向恶化。

```text
Status: PENDING
Coverage calibration protocol: TODO
Strongest learned control: TODO
Decision evidence: TODO
```

---

## 10. G6 — Sequential and OOD Evaluation

### 10.1 假设 H3-b

CAIR 在 receding-horizon 执行中可将短视野 influence prior 转化为 horizon 2–6 的最终恢复收益，并对未见内容和退化条件保持有效。

### 10.2 固定测试轴

```text
Episode horizon: 2, 3, 4, 5, 6
ID content: held-out DIV2K
OOD content: Kodak24, BSD100
OOD degradation: unseen severity
Compositional: seen pair -> unseen ordered pair; pair -> triple
Optional transfer: executor checkpoint/backbone B
```

### 10.3 结果表

| Setting | H | CAIR gain | Strongest control gain | Paired delta | 95% CI | Coverage | Harm rate | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| ID | 2 | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |
| ID | 3 | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |
| ID | 4 | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |
| ID | 5 | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |
| ID | 6 | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |
| unseen severity | TODO | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |
| unseen pair | TODO | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |
| pair -> triple | TODO | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |
| Kodak24 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |
| BSD100 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | PENDING |

### 10.4 PASS 条件

- ID horizon 2、4、6 上相对 strongest control 的三个 seed paired mean effect 均为正。
- Horizon 增长时不得出现 CAIR 在 H≥4 系统性低于 gain-only prior 的反转。
- 至少 unseen severity 与一个内容 OOD 数据集通过 matched-coverage 比较。
- 仅当 unseen-pair 和 pair-to-triple 均通过时，才允许使用“compositional influence generalization”表述。
- 跨 executor 失败不影响单 executor claim，但必须删除 executor-agnostic 表述。

```text
Status: PENDING
Final claim boundary: TODO
Decision evidence: TODO
```

---

## 11. 每次回填格式

```text
Experiment ID:
Gate / experiment:
Date:
Code commit:
Config hash:
Executor/checkpoint hash:
Dataset and clean-image split:
Number of clean images / states / transitions:
Training seeds:
Primary endpoint:
Per-seed result:
Clean-image paired effect:
Cluster-bootstrap 95% CI:
Coverage / opportunity recall / precision:
Secondary LPIPS/DISTS audit:
Missing/failed samples:
Strongest control:
Allowed conclusion:
Gate recommendation:
Reviewer:
```

禁止只回填均值而不记录数据单位、seed、coverage 和置信区间。