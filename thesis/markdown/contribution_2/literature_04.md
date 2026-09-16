# Fault Tolerance at the High Level

High-level fault tolerance concerns mission-level resilience: the ability of a robotic system to revise task structure, switch strategies, and reason about failure conditions that cannot be solved by local control or simple component restarts. At this level, the question is no longer whether a signal is noisy or whether a driver has crashed, but whether the robot can still accomplish its task safely when plans fail, assumptions change, or unexpected events invalidate its current strategy. The literature consistently shows that architectural choice strongly shapes this capability.

O