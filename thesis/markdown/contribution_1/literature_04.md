# FSMs with LLMs

Finite State Machines (FSMs) remain attractive in robotics because they provide explicit states, explicit transitions, and a control structure that is comparatively easy to verify and debug [Using Finite State Machines in Introductory Robotics: Methods and Applications for Teaching and Learning]. For sequential tasks and safety-critical execution, this explicitness is valuable because failures can often be localized to a specific state, transition condition, or missing event. The difficulty is that conventional FSMs become rigid as tasks, contingencies, and interaction patterns grow more complex. This tension between explicit control and limited adaptability is the main reason recent work has started to combine FSM-based execution with Large Language Models (LLMs).

