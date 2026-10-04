import Foundation
import CoreLocation
import CoreMotion

public protocol ContinuumLocationEngineDelegate: AnyObject {
    func locationEngine(
        _ engine: ContinuumLocationEngine,
        didUpdateLocation location: CLLocation,
        isFallback: Bool,
        state: FallbackState,
        matchResult: MapMatchResult?
    )
    func locationEngine(_ engine: ContinuumLocationEngine, didDetectSurfaceAnomaly eventType: String, severity: Double)
    func locationEngineDidDetectMountShift(_ engine: ContinuumLocationEngine)
    func locationEngine(_ engine: ContinuumLocationEngine, didUpdateDiagnostics diagnostics: EngineDiagnostics)
}

/// Drop-in iOS location fallback engine.
/// Uses CoreMotion (6-DoF accelerometer + gyroscope) and on-device machine learning
/// to maintain turn-by-turn navigation during GNSS blackouts in tunnels and parking garages.
public final class ContinuumLocationEngine: NSObject, CLLocationManagerDelegate {

    public weak var delegate: ContinuumLocationEngineDelegate?

    public var vehicleProfile: VehicleProfile
    public var roadGraphPack: RoadGraphPack?

    private let locationManager = CLLocationManager()
    private let motionManager = CMMotionManager()
    private let portableRunner: PortableTreeRunner

    // State Tracking
    public private(set) var currentState: FallbackState = .gnssHealthy
    public private(set) var currentLat: Double = 0.0
    public private(set) var currentLon: Double = 0.0
    public private(set) var currentSpeedMps: Double = 0.0
    public private(set) var currentBearingDeg: Double = 0.0
    public private(set) var currentUncertaintyM: Double = 5.0
    public private(set) var currentLeanAngleDeg: Double = 0.0
    public private(set) var hasNavigationOrigin: Bool = false
    public private(set) var latestMatchResult: MapMatchResult? = nil

    private var isTracking = false
    private let gnssTimeoutSeconds: TimeInterval = 2.0
    private let gnssAccuracyThresholdM: Double = 25.0
    private var lastFixTimestamp: TimeInterval = 0.0

    // Diagnostics Counters & Latencies
    public private(set) var imuSamplesCount: Int64 = 0
    public private(set) var gnssFixesCount: Int64 = 0
    public private(set) var deadReckonStepsCount: Int64 = 0
    public private(set) var lastInferenceLatencyUs: Int64 = 0
    public private(set) var totalInferenceLatencyUs: Int64 = 0
    public private(set) var lastMapMatchLatencyUs: Int64 = 0
    public private(set) var totalMapMatchLatencyUs: Int64 = 0

    // Re-convergence Blending
    private var recoveryStartTimestamp: TimeInterval = 0.0
    private let recoveryDurationSeconds: TimeInterval = 2.5
    private var recoverySourceLat: Double = 0.0
    private var recoverySourceLon: Double = 0.0

    // IMU Causal Buffer (20 samples at 10 Hz = 2.0 seconds)
    private var imuWindow: [[Double]] = []
    private var lastMotionTimestamp: TimeInterval = 0.0
    private var lastFeatureSampleTimestamp: TimeInterval = 0.0

    // Mount Shift & Gravity Tracking
    private var refGravityX: Double = 0.0
    private var refGravityY: Double = 0.0
    private var refGravityZ: Double = 9.80665
    private var isRefGravitySet: Bool = false

    // Reverse Gear Detection (Parking Profile)
    private var isReverseGearDetected: Bool = false

    public init(
        portableRunner: PortableTreeRunner,
        vehicleProfile: VehicleProfile = .car,
        roadGraphPack: RoadGraphPack? = null
    ) {
        self.portableRunner = portableRunner
        self.vehicleProfile = vehicleProfile
        self.roadGraphPack = roadGraphPack
        super.init()
        self.locationManager.delegate = self
        self.locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        self.locationManager.distanceFilter = kCLDistanceFilterNone
    }

    public func getDiagnostics() -> EngineDiagnostics {
        let avgInf = deadReckonStepsCount > 0 ? totalInferenceLatencyUs / deadReckonStepsCount : 0
        let avgMm = deadReckonStepsCount > 0 ? totalMapMatchLatencyUs / deadReckonStepsCount : 0

        // Approximate memory footprint
        var info = mach_task_basic_info()
        var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size) / 4
        let kerr = withUnsafeMutablePointer(to: &info) {
            $0.withMemoryRebound(to: integer_t.self, capacity: 1) {
                task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
            }
        }
        let memKb = kerr == KERN_SUCCESS ? Int64(info.resident_size / 1024) : 4096

        return EngineDiagnostics(
            imuSamplesCount: imuSamplesCount,
            gnssFixesCount: gnssFixesCount,
            deadReckonStepsCount: deadReckonStepsCount,
            lastInferenceLatencyUs: lastInferenceLatencyUs,
            avgInferenceLatencyUs: avgInf,
            lastMapMatchLatencyUs: lastMapMatchLatencyUs,
            avgMapMatchLatencyUs: avgMm,
            estimatedMemoryKb: memKb,
            currentProfile: vehicleProfile.rawValue,
            currentState: currentState.rawValue
        )
    }

    public func setAnchorOrigin(lat: Double, lon: Double, bearingDeg: Double = 0.0) {
        currentLat = lat
        currentLon = lon
        currentBearingDeg = bearingDeg
        hasNavigationOrigin = true
        currentState = .fallbackActive
        updateMapMatching()

        let clLoc = CLLocation(
            coordinate: CLLocationCoordinate2D(latitude: currentLat, longitude: currentLon),
            altitude: 100.0,
            horizontalAccuracy: 5.0,
            verticalAccuracy: 5.0,
            course: currentBearingDeg,
            speed: 0.0,
            timestamp: Date()
        )
        delegate?.locationEngine(self, didUpdateLocation: clLoc, isFallback: true, state: currentState, matchResult: latestMatchResult)
    }

    public func start() {
        guard !isTracking else { return }
        isTracking = true

        locationManager.requestWhenInUseAuthorization()
        locationManager.startUpdatingLocation()

        if let last = locationManager.location, !hasNavigationOrigin {
            currentLat = last.coordinate.latitude
            currentLon = last.coordinate.longitude
            if last.course >= 0 {
                currentBearingDeg = last.course
            }
            hasNavigationOrigin = true
        }

        // Start CoreMotion device motion at 50 Hz (0.02s)
        if motionManager.isDeviceMotionAvailable {
            motionManager.deviceMotionUpdateInterval = 0.02
            motionManager.startDeviceMotionUpdates(using: .xArbitraryCorrectedZVertical, to: .main) { [weak self] motion, error in
                guard let self = self, let m = motion else { return }
                self.processDeviceMotion(m)
            }
        }
    }

    public func stop() {
        guard isTracking else { return }
        isTracking = false
        locationManager.stopUpdatingLocation()
        motionManager.stopDeviceMotionUpdates()
        imuWindow.removeAll(keepingCapacity: true)
    }

    // MARK: - CoreLocation Delegate

    public func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.last else { return }
        gnssFixesCount += 1
        let now = Date().timeIntervalSince1970
        lastFixTimestamp = now

        let isAccurate = location.horizontalAccuracy > 0 && location.horizontalAccuracy <= gnssAccuracyThresholdM
        if isAccurate {
            if currentState == .fallbackActive {
                // Initiate smooth recovery blending
                currentState = .recovering
                recoveryStartTimestamp = now
                recoverySourceLat = currentLat
                recoverySourceLon = currentLon
            }

            if currentState == .recovering {
                let elapsed = now - recoveryStartTimestamp
                if elapsed >= recoveryDurationSeconds {
                    currentState = .gnssHealthy
                    currentLat = location.coordinate.latitude
                    currentLon = location.coordinate.longitude
                } else {
                    let alpha = min(max(elapsed / recoveryDurationSeconds, 0.0), 1.0)
                    currentLat = (1.0 - alpha) * recoverySourceLat + alpha * location.coordinate.latitude
                    currentLon = (1.0 - alpha) * recoverySourceLon + alpha * location.coordinate.longitude
                }
            } else {
                currentState = .gnssHealthy
                currentLat = location.coordinate.latitude
                currentLon = location.coordinate.longitude
            }

            currentSpeedMps = max(location.speed, 0.0)
            if location.course >= 0 && location.speed >= 1.5 {
                currentBearingDeg = location.course
            }
            currentUncertaintyM = max(location.horizontalAccuracy, 2.0)
            hasNavigationOrigin = true

            updateMapMatching()

            let blended = CLLocation(
                coordinate: CLLocationCoordinate2D(latitude: currentLat, longitude: currentLon),
                altitude: location.altitude,
                horizontalAccuracy: currentUncertaintyM,
                verticalAccuracy: location.verticalAccuracy,
                course: currentBearingDeg,
                speed: currentSpeedMps,
                timestamp: location.timestamp
            )
            delegate?.locationEngine(self, didUpdateLocation: blended, isFallback: false, state: currentState, matchResult: latestMatchResult)
        } else {
            currentState = .fallbackActive
        }
    }

    // MARK: - CoreMotion Processing & Dead Reckoning

    private func processDeviceMotion(_ motion: CMDeviceMotion) {
        imuSamplesCount += 1
        let now = Date().timeIntervalSince1970

        // Check for GNSS Outage condition
        let timeSinceFix = now - lastFixTimestamp
        if timeSinceFix > gnssTimeoutSeconds {
            if currentState != .fallbackActive {
                currentState = .fallbackActive
            }
        } else if timeSinceFix > 1.0 && currentState == .gnssHealthy {
            currentState = .outagePending
        }

        // Convert userAcceleration from g's to m/s^2 (g = 9.80665)
        let g = 9.80665
        let ax = motion.userAcceleration.x * g
        let ay = motion.userAcceleration.y * g
        let az = motion.userAcceleration.z * g

        let gx = motion.gravity.x * g
        let gy = motion.gravity.y * g
        let gz = motion.gravity.z * g

        let rotX = motion.rotationRate.x
        let rotY = motion.rotationRate.y
        let rotZ = motion.rotationRate.z

        checkMountShift(gx: gx, gy: gy, gz: gz)
        checkSurfaceShock(verticalLinearAcceleration: az)

        // Parking reverse gear check
        if vehicleProfile == .parking && currentSpeedMps < 0.5 {
            if ay < -1.8 {
                isReverseGearDetected = true
            } else if ay > 1.2 {
                isReverseGearDetected = false
            }
        }

        // Sample at 10 Hz into IMU window
        appendImuSample(ax: ax, ay: ay, az: az, wx: rotX, wy: rotY, wz: rotZ, timestamp: now)

        // Auto anchor to first road node if available
        if !hasNavigationOrigin, let pack = roadGraphPack, imuWindow.count == 20 {
            if let firstNode = pack.nodes.values.first {
                setAnchorOrigin(lat: firstNode.lat, lon: firstNode.lon, bearingDeg: 0.0)
            }
        }

        // Perform dead reckoning step when in fallback
        if currentState == .fallbackActive && hasNavigationOrigin && imuWindow.count == 20 {
            deadReckonStep(yawRateRad: rotZ, timestamp: now)
        }

        // Periodic diagnostics callback
        if imuSamplesCount % 20 == 0 {
            delegate?.locationEngine(self, didUpdateDiagnostics: getDiagnostics())
        }
    }

    private func deadReckonStep(yawRateRad: Double, timestamp: TimeInterval) {
        deadReckonStepsCount += 1
        let dtS = lastMotionTimestamp > 0 ? (timestamp - lastMotionTimestamp) : 0.02
        lastMotionTimestamp = timestamp

        // 1. Integrate yaw rate
        let deltaBearingDeg = yawRateRad * dtS * (180.0 / .pi)
        currentBearingDeg = ((currentBearingDeg + deltaBearingDeg).truncatingRemainder(dividingBy: 360.0) + 360.0).truncatingRemainder(dividingBy: 360.0)

        // 2. Predict speed from edge ML portable tree runner with microsecond timing
        let t0Inf = DispatchTime.now().uptimeNanoseconds
        let features = summarizeImuWindow()
        let prediction = portableRunner.predict(features)
        let t1Inf = DispatchTime.now().uptimeNanoseconds
        lastInferenceLatencyUs = Int64((t1Inf - t0Inf) / 1000)
        totalInferenceLatencyUs += lastInferenceLatencyUs

        var predictedSpeed = prediction.isStopped ? 0.0 : prediction.speedMps

        // Profile-specific compensations
        switch vehicleProfile {
        case .motorcycle:
            // Roll lean decoupling: theta = atan(v * omega / g)
            let g = 9.80665
            let leanRad = atan2(predictedSpeed * yawRateRad, g)
            currentLeanAngleDeg = leanRad * (180.0 / .pi)
        case .parking:
            if predictedSpeed < 0.6 { predictedSpeed = 0.0 }
            if isReverseGearDetected && predictedSpeed > 0.0 {
                predictedSpeed = -predictedSpeed
            }
            currentLeanAngleDeg = 0.0
        default:
            currentLeanAngleDeg = 0.0
        }

        currentSpeedMps = predictedSpeed

        // 3. Propagate WGS-84 coordinates
        let distanceM = currentSpeedMps * dtS
        let headingRad = currentBearingDeg * .pi / 180.0
        let deltaEast = distanceM * sin(headingRad)
        let deltaNorth = distanceM * cos(headingRad)

        let metersPerDegLat = 111132.954
        let metersPerDegLon = 111132.954 * cos(currentLat * .pi / 180.0)

        currentLat += deltaNorth / metersPerDegLat
        currentLon += deltaEast / metersPerDegLon
        currentUncertaintyM += prediction.speedStdMps * dtS

        // 4. Map Matching Soft Snapping
        let t0Mm = DispatchTime.now().uptimeNanoseconds
        updateMapMatching()
        let t1Mm = DispatchTime.now().uptimeNanoseconds
        lastMapMatchLatencyUs = Int64((t1Mm - t0Mm) / 1000)
        totalMapMatchLatencyUs += lastMapMatchLatencyUs

        if let match = latestMatchResult, match.matched, match.matchConfidence >= 0.70, !match.isAmbiguous,
           let snapLat = match.snappedLat, let snapLon = match.snappedLon {
            let snapWeight = 0.15
            currentLat = (1.0 - snapWeight) * currentLat + snapWeight * snapLat
            currentLon = (1.0 - snapWeight) * currentLon + snapWeight * snapLon

            if let roadHdg = match.roadHeadingDeg {
                let diff = abs(((currentBearingDeg - roadHdg + 180.0).truncatingRemainder(dividingBy: 360.0) + 360.0).truncatingRemainder(dividingBy: 360.0) - 180.0)
                if diff < 25.0 {
                    currentBearingDeg = currentBearingDeg * 0.96 + roadHdg * 0.04
                }
            }
        }

        // 5. Notify delegate with synthesized location
        let synthetic = CLLocation(
            coordinate: CLLocationCoordinate2D(latitude: currentLat, longitude: currentLon),
            altitude: 100.0,
            horizontalAccuracy: currentUncertaintyM,
            verticalAccuracy: 3.0,
            course: currentBearingDeg,
            speed: abs(currentSpeedMps),
            timestamp: Date()
        )
        delegate?.locationEngine(self, didUpdateLocation: synthetic, isFallback: true, state: currentState, matchResult: latestMatchResult)
    }

    public func simulateStep(speedMps: Double, yawRateRad: Double, dtS: Double = 0.1) {
        // Exposed for testing and simulated route replay on simulator
        deadReckonStepsCount += 1
        let deltaBearingDeg = yawRateRad * dtS * (180.0 / .pi)
        currentBearingDeg = ((currentBearingDeg + deltaBearingDeg).truncatingRemainder(dividingBy: 360.0) + 360.0).truncatingRemainder(dividingBy: 360.0)
        currentSpeedMps = speedMps

        let distanceM = speedMps * dtS
        let headingRad = currentBearingDeg * .pi / 180.0
        let deltaEast = distanceM * sin(headingRad)
        let deltaNorth = distanceM * cos(headingRad)

        let metersPerDegLat = 111132.954
        let metersPerDegLon = 111132.954 * cos(currentLat * .pi / 180.0)

        currentLat += deltaNorth / metersPerDegLat
        currentLon += deltaEast / metersPerDegLon

        updateMapMatching()

        let synthetic = CLLocation(
            coordinate: CLLocationCoordinate2D(latitude: currentLat, longitude: currentLon),
            altitude: 100.0,
            horizontalAccuracy: currentUncertaintyM,
            verticalAccuracy: 3.0,
            course: currentBearingDeg,
            speed: currentSpeedMps,
            timestamp: Date()
        )
        delegate?.locationEngine(self, didUpdateLocation: synthetic, isFallback: true, state: currentState, matchResult: latestMatchResult)
    }

    private func updateMapMatching() {
        guard let pack = roadGraphPack, hasNavigationOrigin else { return }
        latestMatchResult = pack.match(
            lat: currentLat,
            lon: currentLon,
            headingDeg: currentBearingDeg,
            speedMps: abs(currentSpeedMps)
        )
    }

    /// Matches continuum_idr.features.summarize_window: 6 channels x 7 statistics = 42 features.
    public func summarizeImuWindow() -> [Double] {
        guard !imuWindow.isEmpty else { return [Double](repeating: 0.0, count: 42) }
        var features = [Double](repeating: 0.0, count: 42)
        let sampleCount = Double(imuWindow.count)

        for channel in 0..<6 {
            let values = imuWindow.map { $0[channel] }
            let mean = values.reduce(0.0, +) / sampleCount

            var variance = 0.0
            var energy = 0.0
            var minVal = values[0]
            var maxVal = values[0]

            for v in values {
                let diff = v - mean
                variance += diff * diff
                energy += v * v
                if v < minVal { minVal = v }
                if v > maxVal { maxVal = v }
            }

            let offset = channel * 7
            features[offset] = mean
            features[offset + 1] = sqrt(variance / sampleCount)
            features[offset + 2] = minVal
            features[offset + 3] = maxVal
            features[offset + 4] = values.last ?? 0.0
            features[offset + 5] = (values.last ?? 0.0) - (values.first ?? 0.0)
            features[offset + 6] = sqrt(energy / sampleCount)
        }
        return features
    }

    private func appendImuSample(ax: Double, ay: Double, az: Double, wx: Double, wy: Double, wz: Double, timestamp: TimeInterval) {
        let minInterval: TimeInterval = vehicleProfile == .externalImu ? 0.01 : 0.1
        if lastFeatureSampleTimestamp != 0.0 && (timestamp - lastFeatureSampleTimestamp) < minInterval {
            return
        }
        lastFeatureSampleTimestamp = timestamp

        let sample = [ax, ay, az, wx, wy, wz]
        if imuWindow.count >= 20 {
            imuWindow.removeFirst()
        }
        imuWindow.append(sample)
    }

    private func checkMountShift(gx: Double, gy: Double, gz: Double) {
        if !isRefGravitySet {
            refGravityX = gx
            refGravityY = gy
            refGravityZ = gz
            isRefGravitySet = true
            return
        }

        let normRef = sqrt(refGravityX * refGravityX + refGravityY * refGravityY + refGravityZ * refGravityZ)
        let normCur = sqrt(gx * gx + gy * gy + gz * gz)
        if normRef > 1.0 && normCur > 1.0 {
            let dot = (refGravityX * gx + refGravityY * gy + refGravityZ * gz) / (normRef * normCur)
            let clampedDot = min(max(dot, -1.0), 1.0)
            let angleDeg = acos(clampedDot) * (180.0 / .pi)
            if angleDeg > 15.0 {
                delegate?.locationEngineDidDetectMountShift(self)
            }
        }
    }

    private func checkSurfaceShock(verticalLinearAcceleration: Double) {
        if verticalLinearAcceleration > 4.5 {
            delegate?.locationEngine(self, didDetectSurfaceAnomaly: "SPEED_BREAKER", severity: verticalLinearAcceleration / 12.0)
        } else if verticalLinearAcceleration < -4.0 {
            delegate?.locationEngine(self, didDetectSurfaceAnomaly: "POTHOLE", severity: abs(verticalLinearAcceleration) / 14.0)
        }
    }
}
