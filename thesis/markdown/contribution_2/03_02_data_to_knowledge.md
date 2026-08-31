# Data To Knowledge Store

This document describes how input data is inserted into the experience-side knowledge store. It follows the representation defined in [Knowledge Representation for Robotic Experience](03_01_knowledge_representation.md): two linked graphs that share stable capability and context IDs while keeping their roles separate.

- **Semantic graph** for meaning, relationships, retrieval context, and capability descriptions

- **Statistical graph** for empirical runtime evidence used by planning and RAPFS estimation.

The companion document [Knowledge Store To RAPFS](03_05_knowledge_to_rapfs.md) describes how these stored representations are read back out and used to calculate the Risk-Aware Plan Feasibility Score (RAPFS) for candidate plans.

## Source Inputs

The experience layer receives four main categories of input:

| Input source | Example data | Primary store | Purpose |
|---|---|---|---|
| Supervisor `SystemStatus` messages | capability names, lifecycle state, run evidence, logs, battery intervals, related nodes | statistical graph and selected semantic graph fields | update empirical evidence, capability context, and fault concepts |
| Capability metadata | descriptions, provider names, declared interfaces, dependencies and parameters | semantic graph | support retrieval, matching, and graph reasoning |
| Planner and Fabric history | prior plans, graph edges, success/failure paths, recovery branches | semantic graph and statistical graph | learn relationships and plan-level outcomes |
| External/task context | user task text, environment state, robot state, retrieved documents and executed plan success feedback | semantic graph and statistical graph | condition capability matching and uncertainty estimates |

The supervisor reports observations; the experience layer owns the transforms, accumulation rules, and estimator state. This keeps raw monitoring separate from planning policy. In the current implementation, the supervisor publishes `supervisor_msgs/msg/SystemStatus` on the `system_status` topic, and the experience server subscribes to that topic before converting the capability-centric message into its internal `SystemStatus` structure.

## Ingestion Pipeline

All incoming data should pass through the same stages before it is written to either graph.

1. **Normalize identity.** Resolve capability names, task entities, context entities, and plan node identifiers into stable experience-side IDs.

2. **Classify evidence.** Separate semantic fields from empirical measurement fields. Some records, such as logs, produce both a semantic write and a statistical write.

3. **Attach context.** Add task, environment, robot, mission, and time-window context so future estimates can be conditioned on where the evidence came from.

4. **Validate event semantics.** Apply the current event convention before updating counters: `TRIGGERED` starts a run, `SUCCEEDED` marks success, `FAILED` marks failed completion, and `TERMINATED` marks cancellation or external stop.

5. **Write to the appropriate graph.** Insert descriptive relationships into the semantic graph and accumulated measurements into the statistical graph.

## Semantic Data Write Path

Semantic data describes what entities are and how they relate. It should be inserted into the semantic graph as capability, task entity, context entity, plan pattern, and fault concept nodes, and where useful mirrored into the vector index for text similarity search.

### Semantic Fields From `SystemStatus`

The current supervisor message contributes these semantic fields:

- `capability_name` identifies the capability node,
- `related_nodes[]` creates or updates context entity nodes and dependency or interaction edges,
- `logs[].source` identifies the component that emitted a fault concept,
- `logs[].description` can be embedded for retrieval and clustered into fault concepts,
- `logs[].label` can be stored as categorical metadata on fault nodes and also used statistically as a severity signal.

Capability metadata and planner history add the rest of the semantic structure:
dependency edges such as `capability_depends_on`, interaction edges such as
`capability_interacts_with`, task edges such as `capability_can_do`, and plan
pattern edges that preserve sequences, parallel branches, and recovery paths.

Lifecycle flags and outcome labels are not optimization scalars by themselves, but they are useful provenance and context for retrieval, explanations, and debugging.

## Statistical Data Write Path

Statistical data records how capabilities actually performed. It should be
inserted into a statistical graph keyed by capability and comparable context:
task, environment, robot state, mission state, and estimator time window when
enough data exists. Unlike the semantic graph, the statistical graph stores
numeric evidence and estimator state.

### Supervisor Fields To RAPFS Terms

The current `SystemStatus` message supports the planning vector
$x_i=[p_i,t_i,e_i,f_i,\mathbf{r}_i,u_i]$ as follows:

| RAPFS term | Current support | Supervisor evidence | Experience-side use |
|---|---|---|---|
| $p_i$ | strong | `run_evidence.runs_completed`, `runs_succeeded`, `runs_failed`, `runs_aborted`, `last_outcome_label` | empirical success estimate and consistency checks |
| $t_i$ | partial | `lifecycle.last_start_time`, `lifecycle.last_stop_time`, `battery_usage.run_intervals[].start_time`, `run_intervals[].stop_time` | valid run durations accumulated as count, sum, and sum of squares |
| $e_i$ | strong | `battery_usage.last_delta_percentage`, `cumulative_delta_percentage`, `run_intervals[].delta_percentage` | per-run and aggregate battery or energy evidence |
| $f_i$ | strong | `logs[].label`, optionally `logs[].source` | severity-specific fault counts and exposure-aligned fault burden |
| $\mathbf{r}_i$ | not measured | `related_nodes[]` only as a proxy | resource evidence remains missing until quantitative telemetry exists |
| $u_i$ | indirect | sample counts, missing fields, posterior variance, interval width, retrieval unfamiliarity | statistical, missing-evidence, and unfamiliarity components of uncertainty |

Resource demand $\\mathbf{r}_i$ is not directly measured yet. Until CPU, memory, network, storage, actuator effort, and peak/concurrent usage evidence are available, `related_nodes[]` must be treated only as semantic dependency evidence, not as quantitative resource usage.

### Accumulation Rules

The statistical graph should store accumulated sufficient statistics rather than recomputing estimates from bounded snapshot arrays.

- Success probability uses completed terminal outcomes, not lifecycle stop events alone.

- Runtime uses valid start/stop intervals and should track count, sum, and sum of squares.

- Energy uses per-run battery deltas and should track count, sum, and sum of squares.

- Fault burden uses severity-specific counts and exposure, such as completed runs or accumulated runtime.

- Uncertainty uses sample counts, posterior variances, interval widths, missing-evidence flags, and retrieval unfamiliarity.

- Logs are snapshots, so per-severity fault counts must be accumulated incrementally or published as monotonic counters before old records are trimmed.

## Linking The Two Graphs

The semantic and statistical graphs should share stable IDs for capabilities,
task entities, and context entities. This enables a planning query to first
retrieve semantically relevant capabilities, then join those candidates against their empirical evidence.

The intended pattern is:

1. Semantic graph and vector search identify candidate capabilities and related context.
2. Shared capability and context IDs join each candidate to matching statistical rows.
3. Broader capability or context aggregates are used only when specific evidence is sparse.
4. Estimators produce the planning feature vector $x_i=[p_i,t_i,e_i,f_i,\\mathbf{r}_i,u_i]$.
5. RAPFS combines those feature vectors according to the plan graph semantics.

Keeping the two graphs separate prevents semantic relevance from being confused with empirical reliability. A capability can be highly relevant but unreliable, or statistically strong but semantically irrelevant to the current task.
