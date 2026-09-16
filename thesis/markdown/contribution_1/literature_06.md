## Behaviour Representations in Robotics

### Skill and capability representations in robotics

Representing robot skills, tasks, behaviours, and capabilities has been a recurring problem in robotics, especially when the goal is to build systems that can be reused, inspected, and composed across different applications. Prior work spans rigid instructive systems, which are often easy to reason about but hard to adapt, and more flexible representations that better accommodate real-world variation but can be difficult to ground symbolically \cite{chen2024language, olivares2019review}. For HRI systems, this representation problem matters directly because interaction quality depends on the robot exposing understandable behaviour interfaces while remaining responsive to changing contexts.


### Research gap between symbolic and adaptive systems

The gap between symbolic and adaptive systems is particularly evident when considering the trade-offs 

### The original Capabilities package as prior art


### Behaviour Trees and LLM-assisted planning

The earlier thesis draft also framed this contribution against a more specific planning problem: how to connect behaviour-based robot control architectures with large language models in a way that preserves grounding and execution compatibility. Behaviour Trees are a particularly relevant reference point because they are widely used to structure reusable robot behaviours and increasingly appear in systems that support automatic task generation \cite{cao_robot_nodate, colledanchise2021implementation, biggar_principled_2021}.


### FSM semantics and the case for Fabric

The GPSFSM paper sharpens that argument by comparing Behaviour Trees and Finite State Machines more directly in the context of LLM-based generation. BTs benefit from an established XML representation and strong adoption in robotics, especially through frameworks such as BehaviorTree.CPP and Nav2. Their modularity and verification affordances make them attractive execution substrates. However, the GPSFSM paper argues that BTs still impose semantic overhead on a language model because the model must reason about hierarchical traversal, ticking semantics, and one-parent tree constraints in addition to the task itself.