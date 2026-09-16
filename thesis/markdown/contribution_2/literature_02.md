# Fault Tolerance - Low level
# Fault Tolerance at the Low Level

Low-level fault tolerance addresses the earliest and most physically grounded failure modes in robotic systems. These include actuator degradations such as partial loss of effectiveness, increased friction, or transmission damage; sensor failures such as drift, freeze, bias, or complete dropout; and interaction effects such as wheel slip that appear in data as though they were internal faults. At this layer, the central challenge is to distinguish between normal process variation, environmental disturbance, and genuine component failure quickly enough to preserve safe control. Logical and software anomalies also appear here indirectly, especially when they affect raw telemetry or hardware interfaces, but low-level techniques are primarily centred on numerical consistency and physical behaviour.

