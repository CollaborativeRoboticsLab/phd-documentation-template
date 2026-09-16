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