# Plan Ranking and Selection

Represent each candidate plan as a directed execution graph:

$$
G_\pi=(V_\pi,E_\pi),
$$

where each vertex is a capability or system-runner instance and each directed edge is labeled by its triggering event, such as start, success, failure, or stop. This matches Fabric's internal `Plan`: the parser converts `sequential`, `parallel_all`, `parallel_any`, and `recovery` controls into a map of directed connections. 

A sequential plan $\pi=(c_1,\ldots,c_n)$ is the special case whose graph is a chain and can be represented as a linked list. A general graph with parallel branches cannot be represented by one linked list without losing its branching structure.

Let the planner generate a finite candidate set of plans, each represented as a directed execution graph:

$$
\mathcal{P}=\{G_{\pi_1},G_{\pi_2},\ldots,G_{\pi_m}\}.
$$

And define a feature vector for each capability instance:

$$
x_i = [p_i, t_i, e_i, f_i, \mathbf{r}_i, u_i],
$$

where:

- $p_i$: empirical probability of success,
- $t_i$: expected execution time,
- $e_i$: expected energy or battery cost,
- $f_i$: expected fault burden,
- $\mathbf{r}_i$: a resource-demand vector, such as CPU, memory, bandwidth, storage, and actuator demand,
- $u_i$: normalized epistemic uncertainty combining estimation uncertainty, task ambiguity, unfamiliarity, and missing-evidence penalties.

The terms have distinct roles. In particular, 

- $1-p_i$ is execution-failure risk, not uncertainty, 
- $u_i$ expresses doubt about the available model or
evidence. Random execution variability can be represented separately when a risk-sensitive extension is used.

The plan-selection problem is to rank the candidates and choose the best feasible graph:

$$
G_{\pi^*}=\arg\max_{G_\pi\in\mathcal{P}\cap\mathcal{F}}
\operatorname{RAPFS}(G_\pi),
$$

subject to:

$$
T(G_\pi) \leq T_{\mathrm{avail}}, \quad E(G_\pi) \leq E_{\mathrm{avail}}, \quad
S(G_\pi) \geq \tau, \quad
\mathbf{Q}_{q}\!\left(\mathbf{R}_{\mathrm{peak}}^\omega(G_\pi)\right) \preceq \mathbf{R}_{\max},
$$

where,

- $\operatorname{RAPFS}(G_\pi)$ is the Risk-Aware Plan Feasibility Score,

- $T(G_\pi)$ is expected Timespan, $T_{\mathrm{avail}}$ is the available time budget,
- $E(G_\pi)$ is expected energy cost, $E_{\mathrm{avail}}$ is the available energy budget,
- $\tau$ is the minimum acceptable terminal success probability, and $\mathbf{Q}_{q}(\mathbf{R}_{\mathrm{peak}}^\omega(G_\pi))$ is a componentwise upper quantile of peak concurrent resource demand under the graph's schedule and control-flow semantics, as defined in the RAPFS hard-feasibility set. The relation $\preceq$ denotes a componentwise bound. Consumable resources, such as total transferred bytes or storage growth, should be modeled with separate cumulative budgets rather than folded into the peak-demand vector.

## Current Instantiation Note

Quantitative resource evidence for $\mathbf{r}_i$ is not yet collected: the current `SystemStatus` message exposes only related-node names, not CPU, memory, network, storage, or actuator measurements.

The formulation above is therefore kept general, but during current testing and evaluation the peak-resource constraint is inactive — equivalently, $\mathbf{R}_{\max}=\boldsymbol{\infty}$ — so no plan is filtered on fabricated resource numbers. The absence of resource evidence instead raises the epistemic-uncertainty term $u_i$ through its missing-evidence penalty. Once a resource-measurement tool for ROS systems is available, activating the constraint is a configuration change, not a reformulation.