## Contributions

While achieving the above-mentioned research objectives, the following contributions are made to socially aware robotics research.

1. **Fabric: A behaviour-based planning system with dynamic plan generation** would be the first contribution of this research. The software systems required to implement this system would be sub-contributions, as explained below.

- *Capabilities2 system for ROS2* enables users to describe the robot's functions as capabilities. This is a reimplementation of the Capabilities system \cite{woodall2014ros} for ROS with optimisations and additional features. This system is designed to serve as an abstraction layer for ROS2 interfaces, providing textual descriptions and minimising overhead. It provides capabilities for the Nav2 stack, prompting, audio, and capabilities itself, and can be connected with foundational models due to its self-explanatory nature.

- *Capabilities2 Fabric* is an extension to the capabilities2 system that allows the capabilities to function as a planning system. This system implements execution plan parsing, capability loading, triggering and management. Due to the behaviour-like nature of capabilities, this system can be categorised as a behaviour-based planning system. Utilising its capabilities and prompting, this system can generate and execute new execution plans based on user requirements, enabling dynamic plan generation.

- *Prompt Tools* is a ROS interface that connects robots with foundational models. This toolset supports *chat* and *single prompt* functionality and is compatible with the OpenAI API and the Ollama API. The Capabilities2 system uses this to connect to the LLM systems for plan generation.

2. **A attention management system that allows interaction-based planning** would be the second contribution of this research. The software systems required to implement this system would be sub-contributions, as explained below.

- *Capabilities2 Attention* is an extension to the capabilities2 system that allows the robot system to capture the external stimuli to react to them appropriately. This includes various aspects, including but not limited to tracking humans in the vicinity, gaze tracking, environmental audio evaluation, capabilities2 fabric triggering, preempting, and replanning based on environmental stimuli.

- *Capabilities2 LLM* is a lightweight LLM that is fine-tuned on a dataset with capabilities information and execution plans with descriptions. This is used to provide offline planning capabilities to the capabilities2 system.

3. *An interaction-based social robotic system with long-term planning* would be built utilising the system developed in previous contributions and extended for long-term planning in this contribution. Sub-contributions would be as follows.

- *Long-term planning with resource management* monitors and manages processing and energy consumption based on available resources, allowing for long-term task planning.

- *A user study on the acceptance of an interaction-based planning system* would be conducted to identify the success and acceptance of the system and the changes needed in the available features.
