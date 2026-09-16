# Fault Tolerance at the Middle Level

Middle-level fault tolerance concerns the software and subsystem layer that connects hardware capabilities to task execution. In contemporary robotic systems, this level is heavily shaped by middleware, lifecycle management, subsystem isolation, and recovery orchestration. Within ROS 2, fault tolerance is no longer treated as an afterthought but is embedded into communication policies, managed node states, diagnostics aggregation, and the planning frameworks used by navigation and manipulation stacks. The goal at this layer is not merely to detect physical faults, but to contain failures in communication, timing, perception, planning, and software integration before they propagate across the system.

