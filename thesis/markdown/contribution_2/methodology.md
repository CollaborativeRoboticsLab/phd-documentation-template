## Methodology

This section defines the technical core of Contribution 2. The numbered subsection files are the canonical methodology content for this chapter, and each file covers one bounded part of the Experience planning pipeline.

1. [methodology_01.md](methodology_01.md) defines the dual knowledge representation built from linked semantic and statistical graphs.
2. [methodology_02.md](methodology_02.md) describes how supervisor telemetry, capability metadata, plan history, and task context are inserted into that representation.
3. [methodology_03.md](methodology_03.md) formulates candidate-plan ranking and hard feasibility constraints over Fabric plan graphs.
4. [methodology_04.md](methodology_04.md) specifies the Risk-Aware Plan Feasibility Score and its uncertainty, risk, and weight-adaptation terms.
5. [methodology_05.md](methodology_05.md) explains how retrieved semantic and statistical evidence is transformed into the node features used by RAPFS.
6. [methodology_06.md](methodology_06.md) adds the external plan-feedback path used for calibration and slow weight updates.
7. [methodology_07.md](methodology_07.md) records how the RAPFS formulation addresses issues identified in the CURE framing and what remains to be implemented or validated.

The ordering matters. The section moves from representation, to ingestion, to scoring, to feedback and validation, so the reader can follow how Experience turns raw execution evidence into an auditable pre-execution plan-ranking decision.