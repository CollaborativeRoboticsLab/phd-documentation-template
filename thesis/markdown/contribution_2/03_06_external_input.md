# External Input And Plan Feedback

External input enters the experience layer when information about the task or the executed plan comes from outside the supervisor telemetry stream. This can include the user's task description, environment reports, retrieved documents, operator judgement, or a post-execution label saying whether the task plan actually achieved its intended objective.

This document focuses on plan-success feedback: how an external judgement that a completed plan succeeded, partially succeeded, or failed can be used to improve future RAPFS ranking.

## Feedback Signal

For an executed Fabric graph $G_\pi$, the external feedback record should store:

- planning request ID and candidate plan ID,
- graph structure hash,
- task and context IDs used during scoring,
- selected score components $S,\hat{T},\hat{E},\hat{F},\hat{C}_r,\hat{U}$,
- active estimator, normalizer, and weight versions,
- observed terminal outcome, such as success, failure, or partial success,
- optional human or external-system judgement of plan quality.

The feedback label is plan-level evidence. It should not be confused with a single capability's lifecycle event. For example, a robot may execute every capability without reporting `FAILED`, but the external task can still fail if the delivered object was placed in the wrong location. Conversely, one recovery branch may execute after a local failure while the overall plan still succeeds.

## Updating Component Estimates

The first use of external success feedback is calibration of the component models. The terminal plan outcome updates the statistical graph as plan-level evidence for validating $S(G_\pi)$. If the feedback can be attributed to a specific capability, context, fault concept, or plan pattern, it may also update the corresponding semantic and statistical evidence. If attribution is unclear, the feedback should remain attached to the plan-level record rather than being forced onto a single node.

Component estimates may update continuously:

- $p_i$ and $S(G_\pi)$ calibration use observed success and failure labels,
- $t_i$ uses observed completion time,
- $e_i$ uses observed battery or energy deltas,
- $f_i$ uses observed warnings, errors, and external fault reports,
- $u_i$ uses mismatch between predicted and observed outcomes, missing  evidence, and unfamiliar contexts.

These updates improve the estimated terms in RAPFS without changing the meaning of the weights. In other words, execution feedback should normally make $S(G_\pi)$, $\hat{T}$, $\hat{E}$, $\hat{F}$, and $\hat{U}$ more accurate before it is used to change $w_s,w_t,w_e,w_f,w_r,w_u$.

## Updating Weights From Plan Success Feedback

Weights encode preferences: how much success is worth relative to time, energy, fault burden, resource cost, and uncertainty. External plan-success feedback can update these weights only when the feedback contains information about preference or ranking quality, not merely information about whether a component estimate was wrong.

For example, suppose two feasible plans were available for the same request:

| Plan | Result | Score pattern |
|---|---|---|
| $G_a$ | externally judged successful | slightly slower, lower uncertainty |
| $G_b$ | externally judged unsuccessful | faster, higher uncertainty |

This feedback can be converted into a pairwise preference:

$$
G_a \succ G_b.
$$

At an evaluation epoch boundary, the system can fit weights that make the
preferred plan score higher:

$$
\operatorname{RAPFS}_{w}(G_a)
>
\operatorname{RAPFS}_{w}(G_b).
$$

A simple learning-to-rank objective can use the score difference:

$$
P(G_a \succ G_b)
=\sigma\!\left(\operatorname{RAPFS}_{w}(G_a)
-\operatorname{RAPFS}_{w}(G_b)\right),
$$

where $\sigma$ is the logistic function and $w$ is constrained to be nonnegative, preferably with $\sum_k w_k=1$. The fitted weight vector is then logged as a new weight version and used only in the next evaluation epoch.

## Versioning And Selection Bias

Weight updates must follow the RAPFS epoch discipline. The system should not change weights immediately after each feedback item, because online weight motion makes scores from different decisions incomparable and can hide whether improvement came from better estimates or changed preferences.

The feedback record must log the weight version that selected the executed plan. This matters because feedback is selection-biased: most outcomes come from plans the previous weights already preferred. If adaptive weights are studied, the experiment should include either occasional execution of a non-top-ranked feasible plan or an importance-correction method. Otherwise, the system can reinforce its initial ranking behavior without learning what would have happened under alternatives.

The uncertainty weight needs special care. A realized success/failure label does not directly contain an uncertainty term, so fitting $w_u$ only against task success tends to drive $w_u$ toward zero. For the base experiment, $w_u$ should remain a policy constant, or it should be fitted against a separate calibration target such as intervention requests, operator overrides, aborts, or prediction interval coverage.

## Example

Assume the planner considered two delivery plans:

- $G_a$: navigate by the longer main corridor, then deliver the item,
- $G_b$: take a shorter cluttered route, then deliver the item.

Before execution, $G_b$ receives the higher RAPFS score because it has a lower expected time. The robot executes $G_b$, but the user reports that the plan failed because the cluttered route made the robot arrive too late and the task objective was missed.

The feedback updates the knowledge store in two layers. First, the observed duration, terminal failure, and cluttered-route context update the component evidence for future estimates. Second, at the next weight epoch, the failed ranking can contribute a preference that penalizes the earlier trade-off: the
learner may increase the effective weight on success or uncertainty, or reduce the relative influence of time, if many similar feedback records show that fast but uncertain plans lead to worse externally judged outcomes.

The result is not that one failure immediately rewrites the score. Instead, external plan feedback becomes auditable evidence: it calibrates the component models continuously and may update the RAPFS weights slowly, in versioned epochs, when repeated outcomes show that the current trade-off does not match
observed task success.
