# Literature Review

This section gathers the conceptual background for Contribution 2 and explains why pre-execution plan assessment is necessary for generative robotic systems. The numbered subsection files are the canonical literature content for this chapter, each covering one focused part of the argument.

1. [literature_01.md](literature_01.md) frames fault tolerance within dependability and motivates a layered view of robotic resilience.
2. [literature_02.md](literature_02.md) reviews low-level fault tolerance, including residual-based detection, observer design, filtering, and heterogeneous sensing.
3. [literature_03.md](literature_03.md) examines middle-layer software and subsystem fault tolerance across ROS 2, navigation, manipulation, diagnostics, and log analysis.
4. [literature_04.md](literature_04.md) surveys high-level task-repair and recovery architectures such as behaviour trees, symbolic replanning, HTNs, and formal constraints.
5. [literature_05.md](literature_05.md) extends the review to cognitive fault tolerance for foundation-model-based robotic systems.
6. [literature_06.md](literature_06.md) focuses on UKF-based sensing diagnostics and neural dynamic models for actuator-side monitoring.
7. [literature_07.md](literature_07.md) closes the review by centering pre-execution verification as the direct bridge from fault-tolerance theory to plan assessment.

Taken together, these subsections move from general robotic fault tolerance to the specific verification and reliability questions that motivate Experience and RAPFS.