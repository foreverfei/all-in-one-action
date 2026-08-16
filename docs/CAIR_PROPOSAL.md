# CAIR: Counterfactual Action-Influence Residual Offline RL for All-in-One Image Restoration

> Version: v1.0
>
> Status: G0–G6 experimental proposal
>
> Decision source: `refine-logs/cair/DECISION_LOG.md`
>
> Result ledger: `refine-logs/cair/GATE_RESULTS.md`

---

## 1. Proposal 结论

CAIR 研究一个收缩后的问题：

> 在单一冻结 All-in-One image restoration executor 下，能否从离线反事实 rollout 中学习“当前动作如何改变后续动作的边际收益”，并将该有向 influence 写成 Q-value prior，从而改善选择性动作决策和 horizon 2–6 的序列恢复？

当前方法只包含两项核心设计：

1. **Counterfactual Directed Action Influence**：定义、测量并预测状态条件化的有向动作影响；
2. **Influence-Residual Offline RL**：将解析二步 influence prior 与 Residual IQL 结合，学习未被短视野 prior 覆盖的长期价值。

以下方向不进入本 proposal：

```text
区域异步控制
Hierarchical RL
Pareto/CMDP
动态 reward weight
PPO / MPC
pixel-space 或 latent world model
executor fine-tuning / TTA
多 expert / 多 checkpoint router
动态 prompt 生成
```

---

## 2. 研究边界

## 2.1 Frozen executor

给定唯一冻结执行器：

\[
x_{t+1}=F_\omega(x_t,a_t),
\]

其中：

- \(x_t\)：当前恢复图像；
- \(a_t\)：离散恢复动作；
- \(F_\omega\)：单一 All-in-One restoration model；
- \(\omega\)：训练、验证和测试期间保持冻结。

所有恢复动作共享完全相同的 executor 权重。若 executor API 需要固定 instruction string，则每个 action ID 只映射到一条预注册、不可学习、不可动态生成的执行字符串。策略不输入自由文本，也不优化 prompt。

CAIR 可以包含轻量 predictor、critic 和 action embedding；“单一权重集”约束指恢复执行器只有一套权重，而不是禁止策略网络。

## 2.2 State、action 与预算

状态：

\[
s_t=(x_t,B_t),
\]

其中 \(B_t\) 是剩余 executor 调用预算。

动作集合：

\[
\mathcal A=\{a_1,\ldots,a_K,\mathrm{STOP}\}.
\]

STOP 是终止动作：

\[
F(s,\mathrm{STOP})=s,
\qquad
r(s,\mathrm{STOP})=0.
\]

策略输入不包含：

```text
degradation label
退化参数
clean reference
oracle intermediate
真实 future state
外部 expert 输出
```

## 2.3 有限视野目标

CAIR v1 使用 full-reference PSNR utility：

\[
M(x,x^*)=\operatorname{PSNR}(x,x^*).
\]

执行动作后的即时增量为：

\[
r_t=g_{s_t}(a_t)=M(x_{t+1},x^*)-M(x_t,x^*).
\]

固定 \(\gamma=1\)。因此有限 horizon return 满足：

\[
G_H=\sum_{t=0}^{H-1}g_{s_t}(a_t)
=M(x_H,x^*)-M(x_0,x^*).
\]

这使训练目标与最终 PSNR 增量保持一致，不通过折扣隐式偏好早期动作。

LPIPS 与 DISTS 只作为独立副指标：

\[
M_{LPIPS}=-LPIPS,
\qquad
M_{DISTS}=-DISTS.
\]

CAIR v1 不声称直接优化感知质量。PSNR 提升但 LPIPS/DISTS 系统性恶化时，只允许给出 fidelity-specific claim。

---

## 3. 问题机制

普通 action-value 学习直接估计：

\[
Q(s,a)\approx\text{执行 }a\text{ 后的长期收益}.
\]

但冻结 executor 可以提供更强的离线结构：对于同一个状态，可以实际执行不同动作，观察它们如何改变后续动作的边际收益。

例如，动作 \(a\) 的当前收益可能较小，但它可能显著提高动作 \(b\) 的后续收益；反之，动作 \(a\) 也可能破坏 \(b\) 的适用性。该效应具有：

- 状态相关性；
- 有向性；
- 非对称性；
- 重复动作饱和；
- 可能随内容和退化强度发生符号反转。

CAIR 不预测完整 successor image，也不把该量解释为真实物理因果。正式术语为：

> **executor-induced marginal utility shift**。

---

## 4. Counterfactual Directed Action Influence

## 4.1 单动作增益

对非 STOP 动作：

\[
g_s(a)=M(F(s,a),x^*)-M(s,x^*).
\]

解释：

| \(g_s(a)\) | 含义 |
|---:|---|
| \(>0\) | 当前执行动作提高 PSNR |
| \(<0\) | 当前执行动作损害 PSNR |
| \(\approx0\) | 改变小于可靠测量阈值 |

## 4.2 有向动作影响

定义：

\[
I_s(a\rightarrow b)=g_{F(s,a)}(b)-g_s(b).
\]

展开为：

\[
I_s(a\rightarrow b)
=
\left[M(F(F(s,a),b),x^*)-M(F(s,a),x^*)\right]
-
\left[M(F(s,b),x^*)-M(s,x^*)\right].
\]

解释：

| \(I_s(a\to b)\) | 含义 |
|---:|---|
| \(>0\) | 执行 \(a\) 后，\(b\) 的边际收益增加 |
| \(<0\) | 执行 \(a\) 后，\(b\) 的边际收益下降 |
| \(\approx0\) | \(a\) 对 \(b\) 的边际收益影响不可分辨 |

一般有：

\[
I_s(a\rightarrow b)\neq I_s(b\rightarrow a).
\]

重复动作项也保留：

\[
I_s(a\rightarrow a)=g_{F(s,a)}(a)-g_s(a),
\]

它描述第二次执行同一动作时的持续增益、饱和或反向作用，不能置零。

STOP 相关项按终止语义定义为：

\[
g_s(\mathrm{STOP})=0,
\quad
I_s(a\rightarrow\mathrm{STOP})=0,
\quad
I_s(\mathrm{STOP}\rightarrow b)=0.
\]

## 4.3 状态级 influence graph

每个状态对应：

\[
\mathcal G_s=(\mathcal A,\mathbf g_s,\mathbf I_s),
\]

其中：

- \(\mathbf g_s\in\mathbb R^K\)：动作节点的一步收益；
- \(\mathbf I_s\in\mathbb R^{K\times K}\)：有序动作边的影响；
- 非 STOP 对角项属于有效边；
- STOP 行列固定为零。

CAIR 不要求使用 GNN。当前动作集合较小，直接使用 action-conditioned shared scorer 预测全部节点和边。

---

## 5. 解析二步价值 prior

由 influence 定义可得：

\[
g_{F(s,a)}(b)=g_s(b)+I_s(a\rightarrow b).
\]

因此，对非 STOP 动作，真实二步最优价值为：

\[
Q_2^*(s,a)
=
g_s(a)
+
\max_{b\in\mathcal A_{feasible}(F(s,a))}
\left[g_s(b)+I_s(a\rightarrow b)\right].
\]

这等价于：

\[
Q_2^*(s,a)
=
\max_b\left[M(F(F(s,a),b),x^*)-M(s,x^*)\right].
\]

STOP 是终止动作：

\[
Q_2^*(s,\mathrm{STOP})=0.
\]

该等式给出 CAIR 的关键结构：不需要预测 future pixels，只需预测当前 gain 和 directed influence，即可恢复解析的 horizon-2 value prior。

---

## 6. 离线反事实数据构造

## 6.1 State bank

初始图像由 clean image 经过固定的 mixed-degradation program 生成。degradation metadata 只用于数据生成和审计，不进入策略输入。

为覆盖真实可达状态，从每个初始状态生成固定随机 action prefixes：

```text
depth 0: mixed-degradation source
depth 1–5: frozen executor 的可达中间状态
```

每个状态保存：

```text
state_id
clean_id
source/degradation_program_id
state depth
remaining budget
action history（仅 metadata，不必作为模型输入）
current image hash
executor/checkpoint/config hash
```

train/val/test 必须在 `clean_id` 级隔离。同一 clean image 的全部退化版本、状态和轨迹只能位于一个 split。

## 6.2 Oracle branches

对每个状态 \(s\)，计算全部一步分支：

\[
s_a=F(s,a),\qquad a\in\mathcal A\setminus\{STOP\}.
\]

由此得到全部 \(g_s(a)\)。

对有序动作对计算：

\[
s_{ab}=F(s_a,b).
\]

由此得到 \(I_s(a\to b)\)。完整枚举每个状态需要约：

\[
K+K^2
\]

次冻结 executor 前向。

## 6.3 计算量控制

固定三层策略：

1. **G0/G1 audit set**：完整枚举全部 \(K^2\) ordered pairs；
2. **训练 state bank**：全部一步动作 + 分层采样 successor action，每个 predecessor 至少采样 4 个 \(b\)，并保证所有 ordered pairs 在 clean-image 级均衡覆盖；
3. **validation/test**：完整枚举 \(K^2\)，用于精确 Q2、ranking 和 shuffle 对照。

全部 successor 按输入 hash、action ID、checkpoint hash 和 preprocessing hash 缓存。训练阶段无 executor 反向传播。

## 6.4 Offline transition dataset

Residual IQL 使用：

\[
\mathcal D=\{(s,a,g_s(a),s',d,B_t)\}.
\]

state bank 中每个采样状态尽量保留全部 first-action transitions，使离散动作支持接近完整。长 horizon 状态由固定、metric-agnostic 的随机 action prefix 产生，不使用 degradation label 或 oracle 最优动作作为 behavior policy 输入。

---

## 7. State-Conditioned Influence Predictor

## 7.1 输入与共享结构

状态编码：

\[
z_s=E_\phi(x_s).
\]

动作使用共享 embedding：

\[
e_a=\operatorname{Emb}(a).
\]

Gain predictor：

\[
\hat g_s(a)=h_g(z_s,e_a).
\]

Influence predictor：

\[
\hat I_s(a\rightarrow b)
=
h_I(z_s,e_a,e_b,e_a\odot e_b,e_a-e_b).
\]

固定要求：

- \(E_\phi\) 在所有动作间共享；
- \(h_g\) 在所有动作间共享；
- \(h_I\) 在全部有序动作对间共享；
- 不对称化输入，保留 action order；
- 不使用 K² 个独立 pair heads 作为主方法；
- clean reference、oracle gain 和 future image 不进入输入。

`E_φ` 可以是轻量可训练 state encoder，或冻结 executor feature 加小型 adapter。两种实现必须在 G3 前固定，所有参数匹配控制使用相同 state feature budget。

## 7.2 测量噪声和符号标签

G0 估计：

\[
\epsilon_M=\max(3\sigma_{repeat},10^{-4}\ \mathrm{dB}).
\]

定义 gain/influence 三分类符号：

\[
c(v)=
\begin{cases}
+1,&v>\epsilon_M,\\
0,&|v|\leq\epsilon_M,\\
-1,&v<-\epsilon_M.
\end{cases}
\]

## 7.3 Predictor loss

Gain regression：

\[
\mathcal L_g=\operatorname{Huber}(\hat g_s(a),g_s(a)).
\]

Influence regression：

\[
\mathcal L_I=\operatorname{Huber}(\hat I_s(a\to b),I_s(a\to b)).
\]

Sign loss：

\[
\mathcal L_{sign}=CE(\hat c_I,c(I_s(a\to b))).
\]

解析 Q2 ranking loss：

\[
\hat Q_2(s,a)=\hat g_s(a)+\max_b[\hat g_s(b)+\hat I_s(a\to b)].
\]

对动作对 \((a_i,a_j)\)：

\[
\mathcal L_{rank}
=
\log\left(1+\exp[-y_{ij}(\hat Q_2(s,a_i)-\hat Q_2(s,a_j))]\right).
\]

总损失：

\[
\mathcal L_{pred}
=
\lambda_g\mathcal L_g
+
\lambda_I\mathcal L_I
+
\lambda_s\mathcal L_{sign}
+
\lambda_r\mathcal L_{rank}.
\]

主 predictor 先独立训练，G3 PASS 后冻结。当前不联合更新 predictor 与 critic，避免 RL loss 改写 influence 语义。

---

## 8. Counterfactual Q Prior

对非 STOP 动作：

\[
P_{CF}(s,a)
=
\hat g_s(a)
+
\max_{b\in\mathcal A_{feasible}(F(s,a))}
\left[\hat g_s(b)+\hat I_s(a\to b)\right].
\]

对 STOP：

\[
P_{CF}(s,STOP)=0.
\]

当执行 \(a\) 后没有剩余预算时，第二步 feasible set 只包含 STOP，故：

\[
P_{CF}(s,a)=\hat g_s(a).
\]

主方法固定使用 hard max。LSE、top-k 或 expectile aggregator 仅作为 G4 通过后的消融，不用于补救主方法失败。

---

## 9. Influence-Residual IQL

## 9.1 Q 分解

对非 STOP 动作：

\[
Q_\theta(s,a)
=
\operatorname{sg}[P_{CF}(s,a)]
+
\Delta Q_\theta(z_s,e_a,B_t).
\]

对 STOP：

\[
Q_\theta(s,STOP)=0.
\]

其中：

- `sg` 阻断 prior 的梯度；
- predictor 在该阶段冻结；
- \(\Delta Q\) 只学习 horizon >2、高阶相互作用、predictor error 和分布偏移造成的剩余价值；
- novelty 不建立在 residual architecture 本身。

## 9.2 IQL objective

Expectile value loss：

\[
\mathcal L_V
=
\mathbb E_{(s,a)\sim\mathcal D}
\left[
L_2^\tau(Q_{\bar\theta}(s,a)-V_\psi(s))
\right].
\]

Bellman target：

\[
y(s,a)=g_s(a)+(1-d)V_{\bar\psi}(s').
\]

Q loss：

\[
\mathcal L_Q
=
\operatorname{Huber}(Q_\theta(s,a),y(s,a)).
\]

主方法损失：

\[
\mathcal L_{CAIR}=\mathcal L_Q+\lambda_V\mathcal L_V.
\]

当前不加入特殊 residual anchor、动态 reward 或额外 contract loss。所有方法使用相同 replay data、state feature、target update、optimizer 和训练步数。

## 9.3 Policy extraction

由于动作离散且 state bank 尽量提供完整 first-action support，主方法直接使用 Q-greedy selective policy，不额外训练 actor：

\[
a^*(s)=\arg\max_{a\neq STOP}Q_\theta(s,a).
\]

给定 validation 校准阈值 \(\delta\)：

\[
\pi(s)=
\begin{cases}
a^*(s),&Q_\theta(s,a^*)>\delta\ \text{且}\ B_t>0,\\
STOP,&\text{otherwise}.
\end{cases}
\]

默认工作点可以使用 \(\delta=0\)，正式比较必须在 validation 上固定阈值并报告完整 threshold sweep。

---

## 10. 推理流程

```text
当前图像 x_t + 剩余预算 B_t
            │
            ▼
共享 state encoder E_phi
            │
            ├── gain predictor: g_hat(s,a)
            └── influence predictor: I_hat(s,a→b)
                            │
                            ▼
                    analytic P_CF(s,a)
                            │
                            ▼
              P_CF + residual critic ΔQ
                            │
                            ▼
             best non-STOP action vs threshold
                  │                    │
                  ▼                    ▼
            execute once              STOP
                  │
                  ▼
            observe next image
```

测试阶段：

- 不使用 clean reference；
- 不运行 oracle metric；
- 不执行 counterfactual executor branches；
- 不预测 future pixels；
- 每一步只调用一次最终选中的 frozen executor；
- predictor 的 \(K^2\) action-pair scoring 仅为轻量网络计算。

---

## 11. 研究假设

## H1 — Influence existence

冻结 executor 上存在超过测量噪声、具有方向性和状态变化的：

\[
I_s(a\to b).
\]

需要排除“只是一张全局 static pair table”的解释。

## H2 — Influence usefulness

相对 gain-only、static pair、feature-concat 和 shuffled controls，正确对齐的 \(\hat I_s(a\to b)\) 能改善：

- Q2 MAE；
- action pair ranking；
- top-1 action accuracy；
- return calibration；
- long-horizon value estimation。

## H3 — Policy improvement

Full CAIR 在 3 seeds、clean-image 级统计上，能够：

- 超过 Always-STOP；
- 超过 predictor-only；
- 超过参数匹配 Direct IQL；
- 超过 gain-only Residual IQL；
- 超过 state-shuffled 和 pair-shuffled prior；
- 在 matched coverage 下保持优势；
- 将优势扩展到 horizon 2–6 和至少一个 OOD 轴。

---

## 12. Mandatory Controls

| ID | 方法 | 核心作用 |
|---|---|---|
| B0 | Always-STOP | 排除保守停止造成的伪增益 |
| B1 | Predictor-only selective | 判断 residual RL 是否必要 |
| B2 | Direct IQL | 标准离线 value baseline |
| B3 | Parameter-matched Direct IQL | 排除参数量增益 |
| B4 | Predictor-feature-concat IQL | 排除额外 feature 增益 |
| B5 | Gain-only Residual IQL | 隔离 directed influence 的作用 |
| B6 | State-shuffled Influence ResIQL | 隔离 state–influence 对齐 |
| B7 | Pair-shuffled Influence ResIQL | 隔离 ordered-pair 语义 |

Predictor-level controls：

```text
global mean
static ordered-pair table
action-only predictor
state-only predictor
K² independent heads
```

Oracle 上界：

```text
oracle gain prior
oracle gain + influence prior
oracle horizon-H action value
```

Oracle 方法不进入可部署方法排名。

---

## 13. 两类 shuffle 的精确定义

## 13.1 State shuffle

\[
\tilde I_s^{state}(a\to b)=\hat I_{\pi(s)}(a\to b).
\]

- clean-image 级 derangement；
- 相同 budget/horizon stratum 内置换；
- gain 保持当前 state；
- 保留动作对位置，只破坏 state 对齐。

## 13.2 Ordered-pair shuffle

- off-diagonal non-STOP pairs 在自身集合内固定 derangement；
- diagonal non-STOP pairs 在自身集合内固定 derangement；
- STOP 行列固定为零；
- 同一 seed 对全部 state 使用同一 permutation；
- 每个 state 的 diagonal/off-diagonal value multiset 保持不变。

这两个控制分别检验 state conditioning 与 directed pair semantics，均属于 admission 必选项。

---

## 14. Selective Policy 评估

定义 horizon-2 opportunity：

\[
O(s)=\mathbb 1\left[\max_{a\neq STOP}Q_2^*(s,a)>\epsilon_M\right].
\]

指标：

\[
Coverage=P(a\neq STOP),
\]

\[
OpportunityRecall=P(a\neq STOP\mid O(s)=1),
\]

\[
BeneficialPrecision=P(Q_2^*(s,a)>\epsilon_M\mid a\neq STOP).
\]

还必须报告：

```text
harmful-action rate
risk–coverage curve
return–coverage curve
area under risk–coverage curve
matched-coverage final gain
LPIPS/DISTS harm audit
```

Matched coverage 要求 coverage 差不超过 2 percentage points；无法直接匹配时，在共同 coverage grid 上插值。不能以更高 STOP 率直接换取更低风险后声称策略优越。

---

## 15. 实验数据与规模

## 15.1 数据划分

正式建议：

| 用途 | 数据 |
|---|---|
| Train | DIV2K train 按固定文件名划分的 700 images |
| Validation | DIV2K train 剩余 100 images |
| ID test | DIV2K validation 100 images |
| OOD content | Kodak24 + BSD100 |

同一 clean image 的全部状态和轨迹不得跨 split。Flickr2K 不在第一轮 admission 中使用，避免在核心机制未成立前扩大数据和计算成本。

## 15.2 分阶段规模

| 阶段 | 建议规模 | 标签策略 |
|---|---:|---|
| G0/G1 audit | 20 clean images，至少 200 states | 全部 \(K^2\) |
| G2/G3 pilot | 200 train images + 50 val images | train 分层 pair sampling；val 全部 \(K^2\) |
| G4/G5 formal | 700 train + 100 val + 100 ID test | test 全部 \(K^2\) |
| G6 OOD | Kodak24 + BSD100 | test 全部 \(K^2\) 或固定完整 action subset |

正式报告总计至少覆盖 224 个外部/ID test clean images，但不同数据集不混合成单一 IID 样本。

## 15.3 训练 seed

固定三个训练 seed。每个 seed 同时控制：

```text
predictor initialization
mini-batch order
critic initialization
state/pair shuffle permutation
```

反事实 executor outputs 和 clean-image split 固定不变，以隔离训练随机性。若后续需要审计 data-generation randomness，另开 data-seed 实验，不与主 3-seed 统计混合。

---

## 16. G0–G6 执行链

| Gate | 核心问题 | 失败处理 |
|---|---|---|
| G0 | executor/STOP/metric/split 是否可靠 | REPEAT；未修复不得继续 |
| G1 | gain/influence/Q2 identity 是否闭包 | REPEAT 或 STOP 数据管线 |
| G2 | state-conditioned directed influence 是否存在 | 不优于 static pair 则 STOP |
| G3 | predictor 是否可学习和泛化 | 不优于 gain/static 则 STOP |
| G4 | influence prior 是否改善 value estimation | 与 shuffle/gain-only 等价则 STOP |
| G5 | 是否超过 Always-STOP 和 matched-coverage controls | 仅靠高 STOP 则不准入 |
| G6 | horizon 2–6 与 OOD 是否成立 | 收缩 claim 或终止序列主张 |

详细指标、阈值和回填表位于 `refine-logs/cair/GATE_RESULTS.md`。

---

## 17. 当前 POC 的定位

已有 30-state、7-image POC：

| Policy | Mean Gain | Std | STOP% |
|---|---:|---:|---:|
| Random | -1.49 | 8.09 | 70.0 |
| Greedy | -3.26 | 11.51 | 3.3 |
| Direct IQL | -0.47 | 5.53 | 43.3 |
| Static ResIQL | -5.09 | 12.90 | 0.0 |
| Dynamic ResIQL | +0.48 | 1.84 | 93.3 |

该结果只支持继续验证，不支持方法 claim。主要原因是 Dynamic ResIQL 约只在 2/30 个状态执行非 STOP 动作，并且未运行 Always-STOP、predictor-only、gain-only、state/pair shuffle、matched coverage 和 3-seed image-level inference。

正式实验不得把该表与 G4/G5 结果合并。

---

## 18. 预期代码结构

```text
cair/
├── data/
│   ├── state_bank.py
│   ├── counterfactual_lattice.py
│   ├── transition_dataset.py
│   └── cache_manifest.py
├── models/
│   ├── state_encoder.py
│   ├── influence_predictor.py
│   ├── counterfactual_prior.py
│   └── residual_iql.py
├── policies/
│   └── selective_q_policy.py
├── analysis/
│   ├── influence_audit.py
│   ├── value_estimation.py
│   ├── risk_coverage.py
│   └── clustered_statistics.py
└── tests/
    ├── test_counterfactual_identity.py
    ├── test_stop_identity.py
    ├── test_shuffle_controls.py
    └── test_split_leakage.py

configs/cair/
├── g0_reliability.yaml
├── g1_closure.yaml
├── g2_influence.yaml
├── g3_predictor.yaml
├── g4_value.yaml
├── g5_selective.yaml
└── g6_sequential_ood.yaml
```

该目录是建议实现入口；正式开发前先完成 G0/G1 tests，不提前实现区域控制或 Model-based 模块。

---

## 19. 两项论文贡献

### Contribution 1 — Counterfactual Directed Action Influence

提出冻结单一 All-in-One executor 下的状态条件化有向动作影响：

\[
I_s(a\to b)=g_{F(s,a)}(b)-g_s(b),
\]

以及对应的反事实 lattice、测量噪声、方向性、sign reversal、state conditioning 和 shuffled-control 协议。

### Contribution 2 — CAIR

由 gain 与 influence 推导解析的 horizon-2 value prior：

\[
P_{CF}(s,a)=\hat g_s(a)+\max_b[\hat g_s(b)+\hat I_s(a\to b)],
\]

并通过：

\[
Q_\theta(s,a)=\operatorname{sg}[P_{CF}(s,a)]+\Delta Q_\theta(s,a)
\]

学习未建模的长视野价值。推理阶段不运行 counterfactual executor branches，仅执行最终选中的一个动作。

---

## 20. Claim 边界与 Stop Rules

| 实验结果 | 允许结论 |
|---|---|
| G2 只发现 static pair effect | 只能研究固定动作顺序，不成立 CAIR state-conditioned claim |
| G3 influence 不可预测 | 测量协议可保留，CAIR 方法终止 |
| G4 Full CAIR 不优于 gain-only | influence edge 对 value estimation 无增益，主方法终止 |
| G4 不优于 pair/state shuffle | 有向或状态结构未被使用，novelty 终止 |
| G5 仅在极低 coverage 有效 | 只允许 selective high-confidence signal，不允许策略改进 claim |
| G5 PASS、G6 FAIL | 可保留单步/receding-horizon selective claim，不声称长序列规划 |
| G6 仅 ID PASS | 只声称 ID sequence improvement |
| unseen pair/triple PASS | 才允许 compositional influence generalization |
| 跨 executor PASS | 才允许 executor-transfer 表述 |

禁止在 Gate 失败后通过更换 DQN/PPO、增加 stop/intensity action、动态 reward、区域 router 或 world model 绕过当前证伪结果。

---

## 21. 最终方法摘要

CAIR 在离线阶段对冻结 All-in-One executor 构造反事实动作 lattice，测量每个动作的一步恢复增益，以及该动作对后续动作边际收益的有向影响。共享 predictor 只根据当前图像和有序动作 IDs 预测 gain 与 influence，并据此恢复解析的 horizon-2 Q prior。Residual IQL 在冻结 prior 之上学习更长 horizon 的未建模价值。推理时，CAIR 对当前状态计算全部轻量 action-pair scores，选择一个超过校准阈值的动作执行，否则停止；不使用退化标签、clean reference、动态 prompt、expert router、test-time adaptation 或 counterfactual executor search。