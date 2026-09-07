# Fault Tolerance with UKF and Neural Dynamic Models

Sensor and actuator faults challenge robotic autonomy in different ways. Sensor faults primarily threaten observability because they corrupt the robot's ability to estimate state, while actuator faults threaten controllability because they distort the relationship between commanded behaviour and realised motion. A practical fault-tolerance architecture therefore benefits from combining model-based state-estimation checks with data-driven models of actuator behaviour. One representative combination is the use of unscented Kalman filtering for sensor-side residual analysis together with neural approximations of robot dynamics for actuator monitoring. In ROS 2-based systems, this pairing is attractive because it maps naturally onto existing localisation pipelines on one side and increasingly common learned inverse-dynamics models on the other. [UKF fault-detection source] [NN actuator-monitoring source]

The case for the unscented Kalman filter begins with the limitations of linearized estimation. Extended Kalman filters approximate nonlinear process and observation models through first-order Taylor expansion, which can introduce bias when the system dynamics are strongly nonlinear. In mobile manipulation, such nonlinearities appear not only in base kinematics but also in the coupling between manipulator dynamics, payload variation, and platform motion. If the estimator itself becomes biased, residual-based fault detection becomes unreliable because a healthy sensor may appear faulty simply because the predictor is inaccurate. The unscented Kalman filter avoids explicit linearization by propagating a set of sigma points through the nonlinear dynamics. For an $L$-dimensional state with mean $\bar{x}$ and covariance $P_x$, the sigma-point set is constructed as

$$
\mathcal{X}_0 = \bar{x},
$$

$$
\mathcal{X}_i = \bar{x} + \left(\sqrt{(L+\lambda)P_x}\right)_i, \quad i = 1, \dots, L,
$$

$$
\mathcal{X}_{i+L} = \bar{x} - \left(\sqrt{(L+\lambda)P_x}\right)_i, \quad i = 1, \dots, L,
$$

where $\lambda = \alpha^2(L+\kappa)-L$ defines the spread of the points. These points are propagated through the full nonlinear model rather than a linear approximation, which generally improves consistency for fault-sensitive state estimation.

Residual-based sensor diagnosis then follows from the innovation sequence. If $z_k$ is the measurement at time $k$ and $\hat{z}_k$ is the predicted measurement, the innovation is

$$
\nu_k = z_k - h(\hat{x}_{k|k-1}).
$$

Under nominal conditions, this innovation should remain approximately zero-mean with covariance

$$
S_k = H_k P_{k|k-1} H_k^T + R_k.
$$

Because the magnitude of the raw innovation depends on both measurement units and changing uncertainty, practical fault detection usually normalizes it with the squared Mahalanobis distance,

$$
d_k^2 = \nu_k^T S_k^{-1} \nu_k.
$$

This produces a statistically interpretable anomaly score and allows thresholding through a chi-square test rather than an arbitrary residual limit. The appeal of this formulation is that it adapts naturally to changing uncertainty: when the estimator is confident, smaller deviations can be flagged, while high process noise or rough terrain enlarge the acceptance region and reduce false positives.

Within ROS 2, the main implementation difficulty is not the filter mathematics but access to the right residual information. Packages such as robot_localization already provide robust EKF and UKF nodes, yet they do not generally publish the full innovation terms needed for fault monitoring. This creates two architectural patterns. A derived-filter approach exposes internal innovation state directly and is mathematically cleaner, but it increases coupling to internal package details and may be brittle across releases. A passive-listener architecture is more deployable: a monitoring node subscribes to raw sensor topics and to the filtered state estimate, reconstructs an approximate innovation in the relevant measurement space, and computes a conservative Mahalanobis-style score using available covariances. Although approximate, this pattern is often sufficient for detecting hard faults such as spikes, dropouts, or strong bias drift while preserving loose coupling between the monitor and the estimator. [robot_localization reference] [passive listener residual-monitoring reference]

Parameter tuning also determines whether the UKF remains fault-sensitive in practice. If measurement covariance is underestimated, the filter may over-trust the sensor and quickly absorb a drifting signal into the state estimate, causing the residual to collapse after only a brief spike. A more fault-sensitive configuration often relies on slightly stiffer process trust, careful threshold calibration, and selective use of differential fusion modes for sensors such as IMUs. These decisions reveal an important principle: state-estimation quality and fault detectability are not identical optimisation goals, and filters configured for best nominal tracking are not always best for residual-based diagnosis.

Actuator fault detection raises a different question: given the commanded motion and the current state, does the resulting effort or motion remain physically plausible? Inverse-dynamics models provide one answer. In analytical form, expected torque may be represented by

$$
	au_{\mathrm{expected}} = M(q)\ddot{q} + C(q,\dot{q})\dot{q} + G(q) + F(\dot{q}),
$$

where the terms capture inertial, Coriolis, gravitational, and frictional effects. However, these models are often difficult to identify accurately for deployed manipulators because friction, backlash, payload variation, and wear introduce nonlinearities that are hard to parameterize. This motivates learned surrogates in which a neural network approximates the inverse-dynamics relation,

$$
\hat{\tau} = \mathrm{NN}(q_t, \dot{q}_t, \ddot{q}_t, \text{context}),
$$

and the discrepancy between predicted and measured effort becomes the actuator-fault residual.

For embedded robotic systems, neural architecture choice is tightly constrained by real-time execution. Recurrent models such as LSTMs may capture hysteresis and history-dependent effects more naturally, but they complicate deployment because hidden-state management and heavier inference costs are hard to reconcile with deterministic control-loop timing. A multilayer perceptron with an explicit history window often offers a better trade-off. By feeding recent positions, velocities, and derived accelerations into a stateless model, the system preserves much of the relevant temporal context while keeping inference fast and predictable. From an implementation perspective, this aligns well with C++ deployment through LibTorch, where a traced TorchScript model can run inside a ROS 2 node without the unpredictability associated with Python runtime behaviour.

The systems implications of this design are as important as the modelling choices. Real-time deployment requires controlling memory allocation, thread usage, and data-movement overhead. Inference nodes must avoid building training graphs, restrict unnecessary thread parallelism, and minimise copying between ROS messages and tensor representations. Just as importantly, the hardware abstraction layer must actually expose the state needed for diagnosis. In ros2_control-based systems, actuator monitoring is ineffective if the hardware interface exports only position and velocity but not effort, because the learned residual then has nothing meaningful to compare against. This makes fault tolerance partly an interface-design problem: monitoring can only be as informative as the state surfaces provided by the underlying robot stack. [LibTorch deployment reference] [ros2_control effort-interface reference]

Architecturally, the safest arrangement is to keep the fault monitor as a sidecar rather than embedding it directly inside the critical control loop. In such a design, the nominal controller drives the hardware while monitoring nodes subscribe passively to filtered odometry, raw sensors, and joint-state streams and publish their conclusions to diagnostics or supervisory layers. This preserves fault observability without allowing monitoring latency or model failure to destabilize the controller itself. It also reflects a broader design principle in dependable robotics: diagnosis should inform safety and replanning, but it should not become a single point of failure for nominal actuation.

Overall, the literature suggests that a hybrid UKF-plus-neural approach is feasible and well motivated for mobile manipulation and other nonlinear robotic systems. The UKF provides statistically grounded residuals for sensor-side anomaly detection, while learned inverse-dynamics models extend diagnosis to actuator-side degradations that are difficult to capture analytically. The main challenges are not conceptual but practical: obtaining access to the right residual signals, tuning filters for diagnosability rather than only tracking accuracy, constraining learned inference to real-time execution budgets, and ensuring that hardware interfaces expose the measurements required for comparison. These challenges make the approach less of a plug-in algorithm than a carefully engineered monitoring architecture.