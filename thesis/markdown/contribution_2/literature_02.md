# Fault Tolerance - Low level
# Fault Tolerance at the Low Level

Low-level fault tolerance addresses the earliest and most physically grounded failure modes in robotic systems. These include actuator degradations such as partial loss of effectiveness, increased friction, or transmission damage; sensor failures such as drift, freeze, bias, or complete dropout; and interaction effects such as wheel slip that appear in data as though they were internal faults. At this layer, the central challenge is to distinguish between normal process variation, environmental disturbance, and genuine component failure quickly enough to preserve safe control. Logical and software anomalies also appear here indirectly, especially when they affect raw telemetry or hardware interfaces, but low-level techniques are primarily centred on numerical consistency and physical behaviour.

The classical response is analytical redundancy. Instead of relying solely on the robot's own reported state, an external or parallel estimator reconstructs expected behaviour from raw measurements and compares that estimate with the observed outputs. For wheeled mobile robots, the most direct example is a kinematic residual built from raw wheel motion. If the left and right wheel angular velocities are denoted by $\omega_L$ and $\omega_R$, then the chassis linear and angular velocities are estimated by

$$
v(t) = \frac{r}{2}(\omega_R(t) + \omega_L(t)), \qquad \omega(t) = \frac{r}{L}(\omega_R(t) - \omega_L(t)).
$$

These quantities can then be integrated into an independent odometry estimate through

$$
x_{k+1} = x_k + v_k \cos\left(\theta_k + \frac{\omega_k \Delta t}{2}\right) \Delta t,
$$

$$
y_{k+1} = y_k + v_k \sin\left(\theta_k + \frac{\omega_k \Delta t}{2}\right) \Delta t,
$$

$$
	heta_{k+1} = \theta_k + \omega_k \Delta t.
$$

The difference between this reconstructed pose and the robot's reported pose defines a residual that can be thresholded to detect faults. The attraction of this method lies in its low computational cost and physical interpretability, but it is only effective when the compared signals are sufficiently independent.

That independence requirement is critical. If the internal odometry and the external checker are both derived from the same faulty encoder stream, then a common-mode failure can corrupt both estimates simultaneously and leave the residual artificially small. For that reason, serious low-level fault detection cannot stop at simple kinematic consistency. It must incorporate heterogeneous sensing or richer dynamical models. A more complete dynamic formulation expresses the robot motion as

$$
M(q)\ddot{q} + C(q, \dot{q})\dot{q} + G(q) + \tau_d = B(q)\tau - A^T(q)\lambda,
$$

where $M(q)$ is the inertia matrix, $C(q,\dot{q})$ contains Coriolis and centripetal effects, $G(q)$ captures gravitational effects, $\tau_d$ denotes disturbances, and $\tau$ is the input torque vector. In principle, such a model provides richer fault sensitivity because it can expose inconsistencies caused by mechanical degradation rather than only kinematic drift.

In practice, however, exact dynamic models are difficult to identify for deployed robots, particularly when hardware is proprietary or when payload changes alter the effective system parameters. This is one reason data-driven approximators remain attractive at the low level. Neural models such as radial basis function networks or back-propagation networks can be trained on healthy trajectories to learn a mapping from controls and recent sensor histories to expected observations. During operation, the difference between predicted and measured behaviour again serves as a residual. Such methods can improve detection sensitivity across varying manoeuvres, but they also introduce a second model whose own distribution shift and calibration must be managed carefully.

Observer-based approaches remain among the most influential tools for low-level fault isolation. Sliding mode observers are particularly valued because they are robust to bounded uncertainty and can reconstruct fault signals directly from the injection term used to drive estimation error to a sliding surface. In nonlinear settings, the observer can be written as

$$
\dot{\hat{x}} = A\hat{x} + Bu + g(\hat{x}) + L(y - C\hat{x}) + \rho\,\mathrm{sgn}(y - C\hat{x}).
$$

Once the observer reaches the sliding regime, the filtered switching term can be interpreted as an estimate of the fault magnitude. This is valuable not only for detection but also for isolation because the direction and magnitude of the reconstructed signal may identify which actuator channel or sensing axis is degraded. Variants such as adaptive sliding mode observers and fractional-order observers attempt to reduce chattering while preserving robustness, making them better suited to noisy robotic platforms.

Kalman filtering provides a complementary family of methods grounded in probabilistic state estimation. Standard extended Kalman filters remain common, but more specialised variants are often needed for fault-sensitive robotics. Adaptive extended Kalman filters can augment the state with fault parameters or tune their noise models online, while iterated or error-state formulations improve consistency in nonlinear motion. For platforms relying on visual and inertial sensing, multi-state constraint Kalman filters provide an especially valuable reference because they estimate motion from a sliding window of camera poses without explicitly including landmarks in the state vector. In fault detection, this allows visual-inertial odometry to act as an external reference against which wheel or proprioceptive estimates can be checked.

This leads naturally to sensor fusion as a resilience mechanism. In black-box robotic systems, reliability often depends less on any single sensor than on the degree of agreement among heterogeneous sensing channels. Visual-inertial odometry, lidar-based localisation, inertial navigation, and wheel odometry can each serve as partial validators for the others when they are derived from independent raw data. Approaches such as fault-resilient optimal information fusion exploit this by combining multiple local filters while suppressing those whose estimates diverge significantly from the group consensus. In effect, fusion becomes a voting process in which the outlier can be isolated without disabling the entire estimation pipeline.

A further issue at this layer is common-mode failure. If lighting failure blinds both stereo perception and marker tracking, or a power disturbance corrupts both IMU and encoder electronics, then apparent agreement among sensors may be misleading. This is why heterogeneous redundancy remains important. Acoustic monitoring is one example: microphones mounted near actuators can reveal signatures of wear, jamming, or bearing damage through vibration and spectral analysis even when position sensors remain superficially plausible. These additional modalities help break shared failure paths and strengthen the independence assumptions on which residual-based diagnosis depends.

Although low-level fault tolerance is often framed in terms of physical models and numerical observers, modern robotic systems increasingly pair it with semantic log analysis. Hardware and firmware problems frequently surface first as repeated driver warnings, transport errors, or inconsistent state messages rather than as immediately visible dynamic failures. Large-language-model-based log analysis frameworks therefore provide a useful complement to analytical redundancy by interpreting the textual narrative of system health. In a full architecture, low-level fault tolerance is strongest when physics-based residuals, heterogeneous sensing, and log-level anomaly analysis are used together rather than as competing alternatives.