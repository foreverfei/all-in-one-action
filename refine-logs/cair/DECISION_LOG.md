# CAIR Decision Log

> Status: FROZEN FOR G0–G6
>
> Date: 2026-08-16
>
> Scope: Counterfactual Action-Influence Residual Offline RL for a single frozen All-in-One image restoration executor.

本文件记录 CAIR 当前轮次的不可隐式修改决策。任何涉及主效用、状态/动作定义、influence 标签、prior 形式、baseline 或 Gate 的变化，都必须先在本文件新增变更项，再更新 `docs/CAIR_PROPOSAL.md` 与实验配置。

---

## 1. 已固定的研究边界 D1–D5

| ID | 决策 | 固定内容 |
|---|---|---|
| D1 | 唯一准入候选 | CAIR 是当前唯一允许进入方法验证的候选。Model-based transition、MPC、PPO、区域控制和 Pareto-conditioned policy 不并行开发。 |
| D2 | POC 证据边界 | 30-state POC 仅作为“选择性动作信号”，不作为序列策略、长视野规划或泛化证据。 |
| D3 | novelty 锚点 | 核心创新是状态条件化的反事实有向动作影响及其 value prior；Residual IQL 只是承载该 prior 的学习器。 |
| D4 | 方法准入 | 必须在 3 个训练 seed、clean-image 级统计单位上，稳定击败 Always-STOP、predictor-only、参数匹配控制、feature-concat 控制、gain-only prior 和两种 shuffled-prior。 |
| D5 | proposal 边界 | 区域异步决策、Hierarchical RL、Pareto/CMDP、动态 reward weight、pixel/latent world model 均移出当前 proposal。 |

---

## 2. 开放决策 A–D 的最终结论

## A. 主效用函数：修改原推荐

### 决策

CAIR v1 固定使用：

\[
M(x,x^*)=\operatorname{PSNR}(x,x^*)
\]

因此：

\[
g_s(a)=M(F(s,a),x^*)-M(s,x^*)
\]

\[
I_s(a\rightarrow b)=g_{F(s,a)}(b)-g_s(b)
\]

`g` 与 `I` 的单位均为 dB。LPIPS 和 DISTS 作为独立副指标，不进入 v1 的训练标签、reward 或 STOP 阈值。

### 原因

1. 现有 POC 的全部收益与方差均以 PSNR 报告；此时改用 `-LPIPS` 会同时改变标签几何和 STOP 边界，无法判断后续增益来自 influence 结构还是 reward 更换。
2. 当前首要任务是验证状态条件化有向 influence 是否提供稳定信息，主指标必须优先保证低方差、可追溯和与现有结果连续。
3. 当前 proposal 不再声称直接优化“感知质量”。正式 claim 写为“提高 full-reference restoration utility，并审计感知指标”。

### 副指标规则

- LPIPS utility：\(M_{\mathrm{LPIPS}}=-\operatorname{LPIPS}\)。
- DISTS utility：\(M_{\mathrm{DISTS}}=-\operatorname{DISTS}\)。
- G5/G6 必须报告其 episode-level change 和 harm rate。
- PSNR 主结果成立但 LPIPS/DISTS 显著恶化时，不允许给出“总体质量提升”结论，只能报告 fidelity-specific improvement。

### 折扣因子

当前任务是有限预算 episodic decision，固定：

\[
\gamma=1.
\]

原因是增量效用需要保持 telescoping：

\[
\sum_{t=0}^{H-1}g_{s_t}(a_t)=M(s_H,x^*)-M(s_0,x^*).
\]

使用 \(\gamma<1\) 会额外偏好早期改善并改变最终质量目标。计算预算由最大 horizon 和 feasible-action mask 约束，不通过折扣或动态 reward 权重处理。

---

## B. 单步选择与多步序列边界：修改原推荐

### 不采用的方案

不采用“G0–G3 设置 \(\gamma=0\)，再把 influence 作为单步耦合惩罚”的方案。当 \(\gamma=0\) 时，prior 退化为 \(\hat g_s(a)\)，有向 influence 从 value 建模中消失；另行加入耦合惩罚会变成缺乏精确二步解释的启发式项。

### 最终 staging

| 阶段 | Gate | 使用 influence 的方式 | 允许结论 |
|---|---|---|---|
| Measurement | G0–G2 | 构造并审计 oracle \(g_s\) 与 \(I_s\) | 标签与现象是否可信 |
| Predictability | G3 | 预测 \(\hat g_s\)、\(\hat I_s\) 及解析二步价值 | influence 是否可从当前状态学习 |
| Value estimation | G4 | \(P_{\mathrm{CF}}\) 作为 horizon-2 Q prior | influence prior 是否改善 value ranking |
| Selective action | G5 | 基于 horizon-2 prior 选择当前一个动作或 STOP | 是否存在非平凡选择性策略收益 |
| Sequential policy | G6 | receding-horizon 执行，实际 episode horizon 2–6 | 是否形成稳定序列策略与 OOD 泛化 |

G5 每次只执行当前选中的一个动作，然后重新观察状态并重新计算 prior；它是 receding-horizon selective control。只有 G6 通过后才允许声称“序列策略有效”。

### 固定 aggregator 与 STOP

对非 STOP 动作固定：

\[
P_{\mathrm{CF}}(s,a)
=
\hat g_s(a)
+
\max_{b\in\mathcal A_{\mathrm{feasible}}(F(s,a))}
\left[\hat g_s(b)+\hat I_s(a\rightarrow b)\right],
\qquad a\neq\mathrm{STOP}.
\]

STOP 是终止动作，不继续 lookahead：

\[
P_{\mathrm{CF}}(s,\mathrm{STOP})=0.
\]

作为标签约定：

\[
g_s(\mathrm{STOP})=0,
\quad
I_s(a\rightarrow\mathrm{STOP})=0,
\quad
I_s(\mathrm{STOP}\rightarrow b)=0.
\]

当执行 \(a\) 后预算耗尽时，第二步 feasible set 只含 STOP，因此 prior 退化为 \(\hat g_s(a)\)。`log-sum-exp`、expectile 或 top-k aggregation 只能作为 G4 之后的消融，不能替代主定义。

---

## C. Oracle 与 learned influence：接受并细化

### 标签边界

- Oracle \(g_s(a)\) 和 \(I_s(a\rightarrow b)\) 只通过训练/验证阶段的冻结 executor 反事实 rollout 计算。
- Oracle labels 需要 clean reference，但 clean reference 不进入 predictor 输入。
- 测试阶段禁止执行 \(O(|\mathcal A|^2)\) 反事实分支；只使用 learned \(\hat g\) 与 \(\hat I\)。
- Oracle prior 仅作为上界，不属于可部署 CAIR。

### Predictor 结构

不采用“每个动作对一个独立回归 head”。固定为：

\[
z_s=E_\phi(x_s),
\]

\[
\hat g_s(a)=h_g(z_s,e_a),
\]

\[
\hat I_s(a\rightarrow b)=h_I(z_s,e_a,e_b,e_a\odot e_b,e_a-e_b).
\]

其中：

- \(E_\phi\) 是共享 state backbone；
- \(e_a,e_b\) 是动作 ID embedding；
- \(h_g\) 在动作间共享；
- \(h_I\) 在全部有序动作对之间共享；
- 输入顺序不得对称化，必须保留 \(a\rightarrow b\) 与 \(b\rightarrow a\) 的差异。

该结构同时满足参数共享、固定动作集推理和 unseen-pair holdout。K² 独立 heads 只允许作为容量匹配消融。

---

## D. Shuffled-prior：两种均为强制控制

不指定单一 shuffle 作为唯一主对照。状态条件化与有向 pair 语义是两个独立 claim，因此两种 shuffle 都必须进入 D4 admission。

### D-state：state shuffle

目的：破坏“当前状态—影响矩阵”的对应关系，同时保留动作对位置和总体数值分布。

固定实现：

1. 在同一 split 内进行 clean-image 级 derangement；
2. 只在相同 remaining budget / horizon stratum 内交换整张 influence matrix；
3. 一个 clean image 的 influence 不得被交换给其自身派生状态；
4. permutation seed 固定并记录；
5. gain prediction \(\hat g_s\) 保持原状态，不随 influence 一起交换。

\[
\tilde I_s^{\mathrm{state}}(a\rightarrow b)
=
\hat I_{\pi(s)}(a\rightarrow b).
\]

### D-pair：ordered-pair shuffle

目的：保留每个状态的 influence 数值 multiset 和 pair 类型边缘分布，只破坏具体动作对语义。

固定实现：

1. 对全部非 STOP、非对角有序动作对构造固定 derangement \(\rho_{off}\)；
2. 对全部非 STOP 对角项 \((a,a)\) 构造独立固定 derangement \(\rho_{diag}\)；
3. 同一 seed 下所有 train/val/test state 使用相同的两组 permutation；
4. STOP 相关项按定义固定为零，不参与置换；
5. 不重新采样数值，不改变每个状态的 off-diagonal 与 diagonal influence multiset。

非 STOP 对角项不得置零，因为：

\[
I_s(a\rightarrow a)=g_{F(s,a)}(a)-g_s(a)
\]

刻画重复执行同一动作后的饱和、持续增益或反向作用。

\[
\tilde I_s^{\mathrm{pair}}(a\rightarrow b)
=
\begin{cases}
\hat I_s(\rho_{off}(a,b)), & a\neq b,\\
\hat I_s(\rho_{diag}(a,a)), & a=b,\\
0, & a=\mathrm{STOP}\ \text{or}\ b=\mathrm{STOP}.
\end{cases}
\]

CAIR 必须同时优于 state-shuffled 与 pair-shuffled prior，才能支持“state-conditioned directed influence”这一完整 claim。

---

## 3. 固定方法公式

\[
g_s(a)=M(F(s,a),x^*)-M(s,x^*)
\]

\[
I_s(a\rightarrow b)=g_{F(s,a)}(b)-g_s(b)
\]

\[
P_{\mathrm{CF}}(s,a)
=
\hat g_s(a)
+
\max_b\left[\hat g_s(b)+\hat I_s(a\rightarrow b)\right],
\quad a\neq\mathrm{STOP}
\]

\[
P_{\mathrm{CF}}(s,\mathrm{STOP})=0
\]

\[
Q_\theta(s,a)
=
\operatorname{sg}[P_{\mathrm{CF}}(s,a)]
+
\Delta Q_\theta(s,a),
\quad a\neq\mathrm{STOP}
\]

\[
Q_\theta(s,\mathrm{STOP})=0.
\]

对于非 STOP 动作，真实 oracle 二步关系为：

\[
Q_2^*(s,a)
=
g_s(a)+\max_b\left[g_s(b)+I_s(a\rightarrow b)\right].
\]

它等价于从状态 \(s\) 先执行 \(a\)，再选择最佳第二步动作的最终 PSNR 增量，是 CAIR prior 的依据。

---

## 4. Admission 的不可放宽条件

CAIR 只有同时满足以下条件才进入论文主方法：

1. G0–G3 全部 PASS；
2. 3 个独立训练 seed 上，CAIR 相对所有 mandatory controls 的 clean-image paired mean effect 同号且为正；
3. 相对验证集选出的 strongest learned control，clean-image cluster bootstrap 95% CI 下界大于 0；
4. 在 matched coverage 或完整 risk–coverage 曲线上仍优于 predictor-only 和 Direct IQL；
5. 不是通过接近 Always-STOP 的 coverage 获得虚假低风险；
6. pair-shuffle 与 state-shuffle 均显著降低 value ranking 或 policy return；
7. LPIPS/DISTS 审计未显示系统性反向恶化。

任一核心条件失败时，必须在 `GATE_RESULTS.md` 记录 `FAIL/STOP`，不得通过替换 RL 算法、动态调 reward 或增加新模块绕过。

---

## 5. Change control

后续需要修改本文件时，追加以下记录：

```text
Change ID:
Date:
Affected decision/formula/gate:
Old definition:
New definition:
Evidence requiring change:
Affected configs/results:
Whether previous results remain comparable:
Decision owner:
```

未经记录的口头调整不构成正式实验协议。