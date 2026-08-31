# Risk-Aware Plan Feasibility Score (RAPFS)

Each Fabric plan is a directed execution graph $G_\pi=(V_\pi,E_\pi)$ whose edges carry Fabric events such as start, success, failure, and stop. Fabric's `parallel_all`, `parallel_any`, and `recovery` controls determine which nodes execute and when. A sequential plan is the chain-graph special case. The **Risk-Aware Plan Feasibility Score (RAPFS)**, will be used to rank a set of candidate plans and select the best one. 

## RAPFS Definition

Lets define RAPFS as a normalized score:

$$
\operatorname{RAPFS}(G_\pi)
= w_s S(G_\pi)
- w_t \hat{T}(G_\pi)
- w_e \hat{E}(G_\pi)
- w_f \hat{F}(G_\pi)
- w_r \hat{C}_r(G_\pi)
- w_u \hat{U}(G_\pi),
$$

where,
- $S(G_\pi)\in[0,1]$ is estimated terminal success,
- $\hat{T}(G_\pi)$ is normalized expected timespan,
- $\hat{E}(G_\pi)$ is normalized expected energy,
- $\hat{F}(G_\pi)$ is normalized expected fault burden,
- $\hat{C}_r(G_\pi)$ is a normalized operating cost derived from multidimensional resource use, 
- $\hat{U}(G_\pi)$ is normalized epistemic uncertainty. 
  
Use nonnegative weights, preferably constrained by $\sum_k w_k=1$ for interpretability.

## Path-Dependent Cost Definitions

`Parallel-any` and `Recovery` controls make execution highly path-dependent (e.g., `parallel_any` stops on first success, and `recovery` triggers only on failure). Although `parallel_all` executes all branches on success, it also becomes path-dependent if an early failure aborts the remaining branches. 

Let $\omega$ denote one possible execution scenario and $P(\omega)$ its probability. Because we use expected values ($\mathbb{E}_\omega$), scenarios are naturally weighted by their probability. For example, a rarely triggered recovery path will have a proportionally small impact on the expected cost. Let $V_\omega\subseteq V_\pi$ be the nodes executed in scenario $\omega$, $s_i^\omega$ and $d_i^\omega$ their scheduled start and finish times, and $A_\omega(t)$ the nodes active at time $t$. Then:

$$
T(G_\pi)
=\mathbb{E}_\omega\!\left[
\max_{i\in V_\omega}d_i^\omega
-\min_{i\in V_\omega}s_i^\omega
\right],
$$

$$
E(G_\pi)=\mathbb{E}_\omega\!\left[\sum_{i\in V_\omega}e_i\right],
\qquad
F(G_\pi)=\mathbb{E}_\omega\!\left[\sum_{i\in V_\omega}f_i\right],
$$

and the scenario-level peak resource demand is:

$$
\mathbf{R}_{\mathrm{peak}}^\omega(G_\pi)
=\max_t^{\mathrm{componentwise}}
\sum_{i\in A_\omega(t)}\mathbf{r}_i.
$$

For hard feasibility, use a declared conservative statistic of this random vector, such as a componentwise upper quantile, rather than the sum of all node demands. For a chain, these definitions reduce to summed time, energy, and fault burden with no concurrent resource demand. The scalar $C_r(G_\pi)$ is used only for preference ranking, for example as expected weighted resource-time usage; the resource vector remains intact for feasibility.

Each hatted cost is produced by a declared transform $g_k$ fitted or fixed on a reference data set:

$$
\hat{K}(G_\pi)=g_K(K(G_\pi))\in[0,1],
\qquad K\in\{T,E,F,C_r,U\}.
$$

The transform, clipping policy, and reference population must be held fixed during an evaluation. Otherwise, the weights do not have stable meanings and scores are not comparable across experiments. Controlled updates across evaluation epochs are governed by the Weight Adaptation Policy section below.

## Graph Success Prediction

Define terminal success as reaching the graph's successful terminal condition:

$$
S(G_\pi)
=P(Y_{\mathrm{terminal}}=1\mid G_\pi,z),
$$

where $z$ contains task, provider, environment, and robot context. Node-level models should be conditional on graph predecessors and context:

$$
P(Y_i=1\mid Y_{\operatorname{pa}(i)},z_i,G_\pi).
$$

Evaluate $S(G_\pi)$ by exact graph inference when practical or by Monte Carlo
simulation over execution scenarios. The graph semantics matter:

- `sequential` chain succeeds when every critical node succeeds,
- `parallel_all` succeeds when all required branches satisfy the join,
- `parallel_any` succeeds when at least one required branch satisfies the join,
- `recovery` succeeds when the primary path succeeds or an enabled recovery path reaches the continuation condition.

The product $\prod_i p_i$ is valid only for a critical chain under the stated conditional-independence approximation. It must not be applied to every node in a parallel or recovery graph.

Calibrate $S$ against observed terminal plan outcomes because this is the component intended to be interpreted as a probability.

## Risk-Sensitive Extension

Execution-outcome variability is distinct from epistemic uncertainty. If the experiment includes a risk-sensitive extension, define the random realized score $Y(G_\pi)$ as:

$$
Y(G_\pi)
= a\,\mathbf{1}_{\mathrm{success}}
- b\,T^{\mathrm{obs}}(G_\pi)
- c\,E^{\mathrm{obs}}(G_\pi)
- d\,F^{\mathrm{obs}}(G_\pi)
- q\,C_r^{\mathrm{obs}}(G_\pi),
$$

and score it with:

$$
\operatorname{RAPFS}_{\mathrm{risk}}(G_\pi)
= \operatorname{RAPFS}(G_\pi)
- \eta\,\widehat{\operatorname{Var}}(Y(G_\pi)),
$$

where $a,b,c,d,q>0$, $\eta\geq0$, and the variance is normalized to a declared scale. The notation $Y$ avoids overloading $\mathbf{R}$, which is reserved for resource demand.

This variance term models instability in realized outcomes. It must not be presented as the same quantity as $\hat{U}(G_\pi)$, which models lack of knowledge about estimates or context. The base experiment can omit this extension and use $\operatorname{RAPFS}$ alone.

## Structured and Calibrated Uncertainty

For capability instance $i$, retain separate normalized components before combining them:

$$
u_i
= \alpha u_i^{\mathrm{stat}}
+ \beta u_i^{\mathrm{amb}}
+ \gamma u_i^{\mathrm{unfam}}
+ \delta u_i^{\mathrm{miss}}
$$

where:

- $u_i^{\mathrm{stat}}$ captures uncertainty caused by sparse or noisy empirical evidence,
- $u_i^{\mathrm{amb}}$ captures ambiguity in the task or capability interpretation,
- $u_i^{\mathrm{unfam}}$ captures out-of-distribution context relative to retrieved vector and graph neighbors,
- $u_i^{\mathrm{miss}}$ captures penalties for missing telemetry or weak observability,
- all components lie in $[0,1]$, and $\alpha,\beta,\gamma,\delta\geq0$ with $\alpha+\beta+\gamma+\delta=1$.

Execution failure probability is represented by $p_i$ and is not inserted again as $1-p_i$ in $u_i$. Environmental randomness and variability in observed
outcomes are retained separately for the optional variance term in the Risk-Sensitive Extension section above. This prevents the objective from counting the same failure risk in the success, uncertainty, and variance terms without an explicit modeling reason.

An initial statistical component can combine normalized interval widths:

$$
u_i^{\mathrm{stat}}
= \rho_p h_p(\mathrm{CIWidth}(p_i))
+ \rho_t h_t(\mathrm{StdErr}(t_i))
+ \rho_e h_e(\mathrm{StdErr}(e_i))
+ \rho_f h_f(\mathrm{StdErr}(f_i)),
$$

where each $h_k$ maps its input to $[0,1]$, the $\rho_k$ are nonnegative and sum to one, and the intervals are computed from accumulated counts, sums, and second moments.

Task ambiguity can be estimated from disagreement between valid task parses or from normalized entropy over candidate interpretations. Unfamiliarity can use the existing vector database and graph retrieval stack:

$$
u_i^{\mathrm{unfam}}
= h_{\mathrm{unfam}}\!\left(
1-\frac{1}{k}\sum_{j=1}^{k}\mathrm{sim}(q_i,z_j)
\right),
$$

where $q_i$ is the current context, $z_j$ are retrieved neighbors, and $h_{\mathrm{unfam}}$ bounds and calibrates the raw distance. Raw cosine distance, graph distance, or RND error is not inherently a probability and must not be treated as one.

The missing-evidence component is:

$$
u_i^{\mathrm{miss}} = \frac{m_i}{M}
$$

where $m_i$ is the number of missing or unusable inputs and $M$ is the number expected by the estimator.

Choose the plan-level aggregation before evaluation. Two useful alternatives are an importance-weighted mean and a critical-step maximum:

$$
\hat{U}_{\mathrm{mean}}(G_\pi)
= \mathbb{E}_\omega\!\left[
\sum_{i\in V_\omega}\lambda_i^\omega u_i
\right],
\qquad \sum_{i\in V_\omega}\lambda_i^\omega=1,
$$

where $\lambda_i^\omega$ are per-scenario importance weights over the executed nodes (written $\lambda$ to avoid overloading $\omega$, which denotes the
scenario), and

$$
\hat{U}_{\mathrm{max}}(G_\pi)
=\max_{i\in V_\pi^{\mathrm{reachable}}}u_i.
$$

The scenario-weighted mean captures expected evidence quality without treating optional recovery nodes as if they always execute. The maximum is conservative:
it prevents one reachable, poorly understood step from being hidden by many familiar steps.

Uncertainty estimators must be calibrated on held-out data against a declared target, such as prediction error, intervention need, or interval coverage. Rank correlation alone does not justify interpreting the result as a probability or applying a fixed execution threshold. Under detected distribution shift, the system should raise the unfamiliarity component and use
a conservative fallback. The estimator interface should consume planner-independent outputs where possible; hidden activations from one LLM are an optional implementation, not an architectural requirement.

## Weight Adaptation Policy

The weights $w_k$ encode preferences (the exchange rate between success probability and time, energy, faults, and uncertainty), while the components encode estimates about the world. New execution data should therefore flow primarily into the component estimates, which improve continuously under fixed weights. Weight evolution is justified only in specific cases: correcting initially misspecified weights against observed outcomes, tracking a genuinely non-stationary trade-off (which is preferably modeled explicitly, for example through a shrinking $E_{\mathrm{avail}}$ or a context-dependent $w(z)$), or compensating stale normalizers (which is preferably fixed by re-fitting $g_K$ at declared checkpoints).

To keep adaptation attributable and the score interpretable, the system adapts in layers with different time constants:

| Layer | What updates | Rate | Mechanism |
|---|---|---|---|
| Component estimates ($p_i$, $t_i$, $e_i$, $f_i$, $u_i$) | Every execution | Fast, continuous | Accumulated counts, sums, and second moments |
| Normalizers $g_K$ | Declared re-fit checkpoints | Slow, versioned | Re-fit on the updated reference population |
| Weights $w_k$ | Between evaluation epochs | Slowest, versioned | Batch re-fit (grid search or pairwise learning-to-rank against realized outcomes $Y$) with a convergence check |
| Constraints ($T_{\mathrm{avail}}$, $E_{\mathrm{avail}}$, $\tau$, $\mathbf{R}_{\max}$) | On mission-context change | Event-driven | Explicit configuration change |

Rules for the weight layer:

- **Epoch discipline.** Weights are frozen within an evaluation epoch and may change only at epoch boundaries. Every planning decision logs the active weight version, and ranking quality is evaluated per weight epoch, never pooled across epochs, because RAPFS values under different weights are not comparable.
- **One layer at a time.** Do not re-fit $g_K$ and $w_k$ in the same epoch boundary; joint drift makes the system unidentifiable.
- **Convergence check.** Persistent weight motion across epochs indicates a modeling problem (misspecified components or unmodeled non-stationarity), not healthy adaptation. Corrections should shrink over time.
- **Selection-bias guard.** Weight re-fits use outcomes of executed plans only, which the previous weights selected. If adaptive weights are studied, include exploration (for example, occasional execution of a non-top-ranked feasible plan) or importance correction; otherwise the fit can lock into a self-confirming region.
- **Uncertainty weight exception.** The realized outcome $Y$ contains no uncertainty term, so fitting $w_u$ against $Y$ drives it to zero. Pin $w_u$ as a policy constant, or fit it against its own calibration target such as intervention or abort events.

**Ablation mechanism: Bayesian posterior over weights.** For the adaptive-weights ablation, maintain a posterior $p(w\mid\mathcal{D}_{1:t})$ over the weight vector, where $\mathcal{D}_{1:t}$ are pairwise outcome comparisons between executed plans (plan $a$ realized a better $Y$ than plan $b$ under the same request), fitted with a logistic likelihood constrained to the simplex. The posterior is updated in batch at epoch boundaries only, respecting the epoch discipline. The posterior mean is logged as the epoch's weight version and used for primary ranking. To satisfy the selection-bias guard, a declared fraction of planning requests may instead rank with a sampled $w\sim p(w\mid\mathcal{D}_{1:t})$ (Thompson sampling), which explores alternative trade-offs in proportion to remaining uncertainty about $w$; every such decision logs the sampled weights. The posterior covariance also provides the convergence check: it should shrink across epochs, and sustained growth or oscillation indicates misspecification.

For the first experiment, fixed weights remain the primary baseline; epoch-updated weights may be reported as an ablation under the versioned-logging discipline above. Fully online, free-running weight updates (for example, exponentiated-gradient or random-walk state-space models) are excluded from the base experiment because they sacrifice identifiability and cross-epoch comparability.


## Hard-Constrained Score

Define the feasible set:

$$
\mathcal{F}=\left\{G_\pi:
T(G_\pi)\leq T_{\mathrm{avail}},\;
E(G_\pi)\leq E_{\mathrm{avail}},\;
S(G_\pi)\geq\tau,\;
\mathbf{Q}_{q}\!\left(\mathbf{R}_{\mathrm{peak}}^\omega(G_\pi)\right)
\preceq\mathbf{R}_{\max}
\right\}.
$$

Any cumulative resource budgets, such as transferred bytes or storage growth, are added as separate constraints. The hard-constrained score is:

$$
\operatorname{RAPFS}_{\mathrm{hard}}(G_\pi)=
\begin{cases}
\operatorname{RAPFS}(G_\pi), & G_\pi\in\mathcal{F},\\
-\infty, & G_\pi\notin\mathcal{F}.
\end{cases}
$$

Here $\mathbf{Q}_q$ is the componentwise resource quantile selected for the deployment risk tolerance. Equivalently, optimize $\operatorname{RAPFS}$ only
over $\mathcal{F}$. A multiplicative zero-one gate is inappropriate because an infeasible plan scored at zero could outrank a feasible plan with negative utility.

> **Current instantiation.** Quantitative resource measurements for $\mathbf{r}_i$ are not yet collected. Until they are, the peak-resource constraint is inactive ($\mathbf{R}_{\max}=\boldsymbol{\infty}$) and the resource-cost weight is set to $w_r=0$ in $\operatorname{RAPFS}$. Missing resource evidence contributes to $\hat{U}$ through the missing-evidence penalty in $u_i$. Activating the constraint later requires only a configuration change.

## Soft-Constrained Score

For optimization that benefits from graded violations, define $[z]_+=\max(0,z)$ and use dimensionless penalties:

$$
\begin{aligned}
\operatorname{RAPFS}_{\mathrm{soft}}(G_\pi)
=\;&\operatorname{RAPFS}(G_\pi)\\
&-\kappa_T\left[\frac{T(G_\pi)}{T_{\mathrm{avail}}}-1\right]_+
-\kappa_E\left[\frac{E(G_\pi)}{E_{\mathrm{avail}}}-1\right]_+\\
&-\kappa_P[\tau-S(G_\pi)]_+
-\sum_{j=1}^{d_r}\kappa_{R,j}
\left[
\frac{Q_q(R_{\mathrm{peak},j}^\omega(G_\pi))}{R_{\max,j}}-1
\right]_+.
\end{aligned}
$$

The $d_r$ resource dimensions retain separate limits and penalties. Additional cumulative budgets receive analogous terms. The hard and soft formulations therefore share one base utility and differ only in constraint handling:

1. **Feasibility layer**: reject plans that violate hard resource or success constraints.
2. **Expected utility layer**: reward likely-successful and efficient plans.
3. **Optional risk layer**: penalize normalized realized-utility variance when that ablation is enabled.

For each planning request, generate the candidate set
$\mathcal{P}=\{G_{\pi_1},\ldots,G_{\pi_m}\}$, discard candidates outside $\mathcal{F}$, rank the remainder by $\operatorname{RAPFS}$, and execute the highest-ranked graph. For the first experiment, use this score with hard feasibility as the primary additive baseline and report the soft formulation as an ablation. Fix normalization transforms and weights on training or validation data, then report success calibration, constraint violations, resource peaks, and each score component separately. This makes later comparison with Bayesian and MDP or POMDP approaches interpretable.