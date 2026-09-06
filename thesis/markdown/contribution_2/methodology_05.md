# Knowledge Store To RAPFS

This document describes how information stored in the experience-side knowledge store is used to calculate the Risk-Aware Plan Feasibility Score (RAPFS). It is the read-side companion to [Data To Knowledge Store](03_02_data_to_knowledge.md), which describes how semantic and statistical evidence are inserted into the representation defined in [Knowledge Representation for Robotic Experience](03_01_knowledge_representation.md).

RAPFS itself is defined in [Risk-Aware Plan Feasibility Score](03_04_risk_aware_plan_score.md). This document focuses on the operational bridge from stored knowledge to the terms in that score.

## Inputs And Outputs

The RAPFS pipeline starts with a planning request and a finite set of candidate Fabric plan graphs:

$$
\\mathcal{P}={G_{\\pi_1},G_{\\pi_2},\\ldots,G_{\\pi_m}\\}.
$$

For each capability instance $i$ in each candidate graph, the knowledge store must provide or estimate the feature vector:

$$
x_i=[p_i,t_i,e_i,f_i,\\mathbf{r}_i,u_i].
$$

The output is a ranked list of feasible candidate plans, with one score and one explanation record per plan:

$$
G_{\pi^*}=\arg\max_{G_\pi \in \mathcal{P}\cap\mathcal{F}}
\operatorname{RAPFS}(G_\pi).
$$

## Read Pipeline

The score calculation should follow a fixed sequence so every plan is evaluated
against the same evidence and normalization rules.

1. **Resolve plan nodes.** Map each Fabric capability instance to a stable capability ID and the relevant task or context entity IDs.

2. **Retrieve semantic context.** Use graph and vector retrieval to confirm task relevance, related task and context entities, dependencies, plan patterns, fault concepts, and unfamiliarity signals.

3. **Join statistical evidence.** Fetch empirical rows for the capability and comparable context using the shared IDs.

4. **Estimate node features.** Convert stored evidence into $p_i,t_i,e_i,f_i,\\mathbf{r}_i,u_i$ with estimators.

5. **Aggregate over graph semantics.** Combine node features according to the candidate plan's sequential, parallel, `parallel_any`, or recovery control flow. 

6. **Apply constraints.** Reject plans outside hard limits before ranking, or apply the declared soft-constraint penalty variant.

7. **Normalize and score.** Apply fixed transforms $g_K$ and fixed score weights $w_k$ for the active evaluation epoch.


## Semantic Retrieval Role

The semantic graph does not directly provide numeric RAPFS costs. Its job is to select and condition the evidence that will be scored.

Semantic retrieval contributes:

- candidate capability matching for the task request,
- related task and context entities,
- plan-pattern context, such as whether a capability is commonly used as a recovery path,
- fault concepts associated with previous executions,
- nearest-neighbor similarity for unfamiliarity estimation,
- explanatory context for why a capability was considered relevant.

The most important rule is that semantic relevance must not be treated as success probability. A highly similar capability is a good candidate to evaluate, but its reliability must come from the statistical graph.

## Statistical Retrieval Role

The statistical graph provides empirical evidence for each RAPFS node feature. Rows should be selected within the active estimator time window using the most specific reliable capability/context key available, with most specific first and broader fallbacks if the specific row is missing or unreliable:

1. capability + matching context entity or edge key,
2. capability + broader context class,
3. capability aggregate,
4. prior/default estimate with high missing-evidence uncertainty.

Fallbacks must be explicit in the explanation record, including the selected key, estimator window, and reason the more specific row was unavailable or unreliable. Moving down the fallback ladder should increase $u_i$: sparse empirical evidence primarily raises $u_i^{\mathrm{stat}}$, missing rows or telemetry raise $u_i^{\mathrm{miss}}$, and context mismatch raises $u_i^{\mathrm{unfam}}$.

## Node Feature Estimation

### Success Probability $p_i$

Use `run_evidence` counters as the primary empirical source:

$$
\hat{p}_i = \frac{\text{runs\_succeeded}}{\max(1,\text{runs\_completed})}.
$$

For uncertainty-aware scoring, the implementation may keep a Beta posterior:

$$
p_i \sim
\mathrm{Beta}(\alpha_0+\text{runs\_succeeded},\; \beta_0+\text{runs\_failed}).
$$

Aborted or externally terminated runs should remain separately available so the
estimator can decide whether to exclude them, penalize them, or model them as a
distinct outcome. The decision must be versioned because it changes score
semantics.

### Expected Time $t_i$

Estimate runtime from valid completed intervals:

$$
t_i^{(k)}=t_{\\mathrm{stop}}^{(k)}-t_{\\mathrm{start}}^{(k)}.
$$

The statistical graph should provide count, sum, and sum of squares so the
estimator can compute a mean, recent-window estimate, upper confidence bound,
or context-conditioned prediction. The active estimator version decides which
summary feeds RAPFS.

### Expected Energy $e_i$

Use per-run battery deltas from `battery_usage.run_intervals[]` or accumulated
energy evidence. As with runtime, the preferred stored state is count, sum, and
sum of squares so the estimate and its uncertainty can be computed without
replaying all raw records.

### Fault Burden $f_i$

Use labeled log events as severity-specific fault evidence. A simple weighted
burden is:

$$
f_i=w_E\\lambda_{\\mathrm{error}}+w_W\\lambda_{\\mathrm{warning}},
$$

where each rate $\\lambda$ is estimated per capability and comparable context
when enough evidence exists. A Gamma-Poisson posterior can supply both the
posterior mean for $f_i$ and posterior variance for statistical uncertainty.

### Resource Demand $\\mathbf{r}_i$

Resource demand should remain a vector, for example:

$$
\\mathbf{r}_i=[\\mathrm{cpu},\\mathrm{memory},\\mathrm{network},\\mathrm{storage},\\mathrm{actuator}].
$$

The current supervisor message does not yet publish quantitative resource
measurements. Until those measurements exist, the resource vector should be
marked missing, the hard resource constraint should remain inactive, and
$w_r=0$ for the resource-cost term. `related_nodes[]` can help identify which
context entities or system components to monitor later, but it is not a
resource measurement.

### Uncertainty $u_i$

Uncertainty is a separate feature, not a copy of execution failure risk. The
recommended decomposition is:

$$
u_i
= \alpha u_i^{\mathrm{stat}}
+ \beta u_i^{\mathrm{amb}}
+ \gamma u_i^{\mathrm{unfam}}
+ \delta u_i^{\mathrm{miss}}.
$$

The knowledge store contributes each component differently:

| Component | Knowledge source | Example signal |
|---|---|---|
| $u_i^{\mathrm{stat}}$ | statistical graph | sparse counts, wide posterior intervals, high standard errors |
| $u_i^{\mathrm{amb}}$ | semantic graph and task parser | disagreement among task interpretations |
| $u_i^{\mathrm{unfam}}$ | semantic graph and vector index | low similarity to retrieved contexts or distant graph neighbors |
| $u_i^{\mathrm{miss}}$ | ingestion/provenance metadata | missing resource telemetry or invalid intervals |

Failure probability is already represented through $p_i$ and plan success
$S(G_\pi)$, so $1-p_i$ should not be inserted again into $u_i$.

## Plan-Level Aggregation

Once each capability instance has a feature vector, the scorer must aggregate over the candidate plan graph rather than flattening it into a list.

### Terminal Success $S(G_\pi)$

Estimate terminal success using the semantics of the Fabric graph:

- a sequential chain succeeds when every required step succeeds,
- `parallel_all` succeeds when all required branches satisfy the join,
- `parallel_any` succeeds when at least one required branch satisfies the join,
- `recovery` succeeds when the primary path succeeds or an enabled recovery
  path reaches the continuation condition.

The product $\prod_i p_i$ is appropriate only for a critical sequential chain under a conditional-independence approximation. Branching and recovery graphs should use exact graph inference when practical, or Monte Carlo simulation over execution scenarios.

### Expected Costs

Let $\omega$ denote an execution scenario and $P(\omega)$ its probability.
Only the nodes that execute in that scenario contribute to its costs:

$$
T(G_\pi)
=\mathbb{E}_\omega\left[
\max_{i\in V_\omega}d_i^\omega
-\min_{i\in V_\omega}s_i^\omega
\right],
$$

$$
E(G_\pi)=\mathbb{E}_\omega\left[\sum_{i\in V_\omega}e_i\right],
\qquad
F(G_\pi)=\mathbb{E}_\omega\left[\sum_{i\in V_\omega}f_i\right].
$$

For resource feasibility, aggregate active concurrent nodes componentwise:

$$
\mathbf{R}_{\mathrm{peak}}^\omega(G_\pi)
=\max_t^{\mathrm{componentwise}}
\sum_{i\in A_\omega(t)}\mathbf{r}_i.
$$

This preserves the difference between cumulative costs, such as energy, and peak concurrent constraints, such as memory or CPU saturation.

### Plan Uncertainty $\hat{U}(G_\pi)$

Plan-level uncertainty should be selected before evaluation. Two supported
options are:

- scenario-weighted mean uncertainty, where rarely triggered branches contribute proportionally less,

- critical-step maximum uncertainty, where one reachable poorly understood step can dominate.

The chosen aggregation rule is part of the scorer configuration and must be
logged with the score.

## Feasibility And Ranking

The hard feasible set is:

$$
\mathcal{F}=\left\{G_\pi:
T(G_\pi)\leq T_{\mathrm{avail}},\;
E(G_\pi)\leq E_{\mathrm{avail}},\;
S(G_\pi)\geq\tau,\;
\mathbf{Q}_{q}\!\left(\mathbf{R}_{\mathrm{peak}}^\omega(G_\pi)\right)
\preceq\mathbf{R}_{\max}
\right\}.
$$

Plans outside $\mathcal{F}$ receive $-\infty$ in the hard-constrained score.
Feasible plans are ranked with:

$$
\operatorname{RAPFS}(G_\pi)
= w_s S(G_\pi)
- w_t \hat{T}(G_\pi)
- w_e \hat{E}(G_\pi)
- w_f \hat{F}(G_\pi)
- w_r \hat{C}_r(G_\pi)
- w_u \hat{U}(G_\pi).
$$

Each hatted cost is normalized by the active fixed transform $g_K$. Normalizersand weights must be frozen within an evaluation epoch so scores remain comparable.

## Score Explanation Record

Every RAPFS calculation should emit an explanation record containing:

- candidate plan ID and graph structure hash,
- selected capability and context IDs,
- evidence rows used for each capability instance,
- fallback level used for each statistical estimate,
- node feature estimates $p_i,t_i,e_i,f_i,\mathbf{r}_i,u_i$,
- plan-level components $S,\hat{T},\hat{E},\hat{F},\hat{C}_r,\hat{U}$,
- feasibility pass/fail status and violated constraints,
- estimator, normalizer, and weight versions,
- missing-evidence and unfamiliarity flags.

This record is necessary for debugging ranking decisions and for later
calibration against observed plan outcomes.

## Current Instantiation

With the current supervisor data, the scorer can compute or estimate:

- $p_i$ from `run_evidence` counters,
- $t_i$ from lifecycle timestamps and run intervals,
- $e_i$ from battery deltas,
- $f_i$ from labeled logs,
- parts of $u_i$ from sample counts, missing evidence, and retrieval
  unfamiliarity after the experience layer has accumulated history.

It cannot yet compute quantitative $\\mathbf{r}_i$. During current evaluation, resource feasibility is inactive, $w_r=0$, and missing resource evidence raises the uncertainty term.
