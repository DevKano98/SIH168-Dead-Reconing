import SwiftUI
import CoreLocation

public struct ContentView: View {

    // Engine & Subsystems
    @State private var engine: ContinuumLocationEngine?
    @State private var bleManager: TrafficBleManager = TrafficBleManager()
    @State private var recorder: TripRecorder?

    // UI Telemetry State
    @State private var speedKmh: Double = 0.0
    @State private var headingDeg: Double = 0.0
    @State private var accuracyM: Double = 5.0
    @State private var currentState: FallbackState = .gnssHealthy
    @State private var isFallbackActive: Bool = false
    @State private var currentLat: Double = 12.8450
    @State private var currentLon: Double = 77.6620
    @State private var currentLeanAngleDeg: Double = 0.0
    @State private var matchedSegmentId: String? = nil
    @State private var matchConfidence: Double = 0.0

    // Diagnostics State
    @State private var infLatencyUs: Int64 = 0
    @State private var avgInfLatencyUs: Int64 = 0
    @State private var estimatedMemoryKb: Int64 = 3450
    @State private var imuSamples: Int64 = 0

    // BLE Stats State
    @State private var bleStats: BleRelayStats = BleRelayStats()
    @State private var bleStatusMessage: String? = nil

    // Config Selection
    @State private var selectedProfile: VehicleProfile = .car
    @State private var selectedRouteScenario: String = "Highway Cruise"
    @State private var isRecording: Bool = false
    @State private var statusText: String = "Ready to record trip"

    // Loaded Assets
    @State private var roadPack: RoadGraphPack?
    @State private var portableRunner: PortableTreeRunner?

    let routeScenarios = [
        "Highway Cruise",
        "City Arterial",
        "Stop & Go Traffic",
        "Potholes & Patched",
        "Speed Breakers",
        "Underpass / Tunnel",
        "Parking Ramp & Reverse",
        "Motorcycle High Lean",
        "Engine Idle Vibration"
    ]

    public init() {}

    public var body: some View {
        ScrollView {
            VStack(spacing: 12) {

                // Top Header Brand Bar
                HStack(alignment: .center, spacing: 6) {
                    Text("CONTINUUM")
                        .font(.system(size: 20, weight: .black))
                        .foregroundColor(.white)

                    Text(" IDR ")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(Color(red: 0.22, green: 0.74, blue: 0.97))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color(red: 0.06, green: 0.16, blue: 0.26))
                        .cornerRadius(4)

                    Text("• SATELLITE FALLBACK SYSTEM")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundColor(Color(red: 0.39, green: 0.45, blue: 0.55))

                    Spacer()
                }
                .padding(.top, 4)

                // State Ribbon Badge
                Text(currentState.title)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background(currentState.badgeColor)
                    .cornerRadius(8)

                // Bento Cluster (3 Hero Cards)
                HStack(spacing: 8) {
                    BentoMetricCard(
                        title: "ESTIMATED SPEED",
                        value: isRecording ? String(format: "%.1f", speedKmh) : "--",
                        unitOrSub: "KM / H",
                        accentColor: Color(red: 0.22, green: 0.74, blue: 0.97)
                    )

                    BentoMetricCard(
                        title: "HEADING",
                        value: isRecording ? String(format: "%03.0f°", headingDeg) : "---°",
                        unitOrSub: cardinalSubtext,
                        accentColor: .white
                    )

                    BentoMetricCard(
                        title: "UNCERTAINTY",
                        value: isRecording ? String(format: "±%.1fm", accuracyM) : "±--m",
                        unitOrSub: roadMatchSubtext,
                        accentColor: Color(red: 0.06, green: 0.73, blue: 0.51)
                    )
                }

                // Interactive Offline Vector Map View
                OfflineMapView(
                    roadPack: roadPack,
                    vehicleLat: currentLat,
                    vehicleLon: currentLon,
                    vehicleHeadingDeg: headingDeg,
                    vehicleUncertaintyM: accuracyM,
                    isFallbackActive: isFallbackActive
                )

                // Map Action Buttons (Anchor & Simulation Step)
                HStack(spacing: 8) {
                    Button {
                        anchorDemoRoute()
                    } label: {
                        Text("Anchor to Demo Route (Indoor Test)")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 38)
                            .background(Color(red: 0.05, green: 0.58, blue: 0.53))
                            .cornerRadius(8)
                    }

                    Button {
                        simulateDrivingStep()
                    } label: {
                        Text("Simulate 2s Step")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.white)
                            .frame(width: 120, height: 38)
                            .background(Color(red: 0.15, green: 0.20, blue: 0.30))
                            .cornerRadius(8)
                    }
                }

                // Apple Maps / iOS Navigation Relay Info Card
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text("NAVIGATION FALLBACK & RELAY")
                            .font(.system(size: 10, weight: .bold))
                            .foregroundColor(Color(red: 0.22, green: 0.74, blue: 0.97))
                            .tracking(0.5)
                        Spacer()
                        Text("iOS CORE")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(.green)
                    }
                    Text("Continuum acts as an in-device inertial provider during GNSS-denied outages (tunnels/underpasses), keeping vector tracking active without cellular data.")
                        .font(.system(size: 11))
                        .foregroundColor(Color(red: 0.58, green: 0.64, blue: 0.72))
                        .lineSpacing(2)
                }
                .padding(12)
                .background(Color(red: 0.06, green: 0.09, blue: 0.16))
                .cornerRadius(10)
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(Color(red: 0.15, green: 0.20, blue: 0.30), lineWidth: 1)
                )

                // Vehicle Profile & Route Scenario Pickers
                HStack(spacing: 8) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("VEHICLE PROFILE")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(Color(red: 0.39, green: 0.45, blue: 0.55))

                        Picker("Profile", selection: $selectedProfile) {
                            ForEach(VehicleProfile.allCases) { profile in
                                Text(profile.displayName).tag(profile)
                            }
                        }
                        .pickerStyle(.menu)
                        .tint(.white)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 6)
                        .background(Color(red: 0.06, green: 0.09, blue: 0.16))
                        .cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(red: 0.15, green: 0.20, blue: 0.30), lineWidth: 1))
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        Text("ROUTE SCENARIO")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(Color(red: 0.39, green: 0.45, blue: 0.55))

                        Picker("Scenario", selection: $selectedRouteScenario) {
                            ForEach(routeScenarios, id: \.self) { scenario in
                                Text(scenario).tag(scenario)
                            }
                        }
                        .pickerStyle(.menu)
                        .tint(.white)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 6)
                        .background(Color(red: 0.06, green: 0.09, blue: 0.16))
                        .cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(red: 0.15, green: 0.20, blue: 0.30), lineWidth: 1))
                    }
                }

                // Action Deck (Start / Stop Trip)
                HStack(spacing: 8) {
                    Button {
                        startTrip()
                    } label: {
                        Text(isRecording ? "RECORDING..." : "START TRIP")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                            .background(isRecording ? Color(red: 0.15, green: 0.20, blue: 0.30) : Color(red: 0.01, green: 0.52, blue: 0.78))
                            .cornerRadius(10)
                    }
                    .disabled(isRecording)

                    Button {
                        stopTrip()
                    } label: {
                        Text("STOP TRIP")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(isRecording ? .white : Color(red: 0.39, green: 0.45, blue: 0.55))
                            .frame(width: 110, height: 48)
                            .background(isRecording ? Color(red: 0.86, green: 0.15, blue: 0.15) : Color(red: 0.10, green: 0.14, blue: 0.20))
                            .cornerRadius(10)
                    }
                    .disabled(!isRecording)
                }

                // Status Text
                Text(statusText)
                    .font(.system(size: 11))
                    .foregroundColor(Color(red: 0.58, green: 0.64, blue: 0.72))
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 2)

                // Diagnostics Telemetry HUD
                VStack(alignment: .leading, spacing: 4) {
                    Text("SYSTEM & INFERENCE TELEMETRY")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(Color(red: 0.39, green: 0.45, blue: 0.55))

                    Text("Inference: \(infLatencyUs) µs (avg \(avgInfLatencyUs) µs) • Heap: ~\(estimatedMemoryKb) KB • IMU: \(imuSamples) samples")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(Color(red: 0.22, green: 0.74, blue: 0.97))
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(10)
                .background(Color(red: 0.06, green: 0.09, blue: 0.16))
                .cornerRadius(8)
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(red: 0.15, green: 0.20, blue: 0.30), lineWidth: 1))

                // Cooperative V2V Traffic Card
                VStack(alignment: .leading, spacing: 8) {
                    Text("COOPERATIVE V2V TRAFFIC (BLE DIRECT 10–30M)")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(Color(red: 0.39, green: 0.45, blue: 0.55))

                    Text("Relay HUD: Sent: \(bleStats.sentCount) | Recv: \(bleStats.receivedCount) | Duplicates: \(bleStats.duplicateCount)")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundColor(Color(red: 0.99, green: 0.88, blue: 0.28))

                    if let msg = bleStatusMessage {
                        Text(msg)
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(Color(red: 0.22, green: 0.74, blue: 0.97))
                    }

                    HStack(spacing: 8) {
                        Button("Trigger Pothole") {
                            triggerBleHazard("POTHOLE", severity: 0.85)
                        }
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity, height: 34)
                        .background(Color(red: 0.05, green: 0.58, blue: 0.53))
                        .cornerRadius(6)

                        Button("Trigger Outage") {
                            triggerBleHazard("GNSS_OUTAGE", severity: 1.0)
                        }
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity, height: 34)
                        .background(Color(red: 0.86, green: 0.15, blue: 0.15))
                        .cornerRadius(6)
                    }
                }
                .padding(10)
                .background(Color(red: 0.06, green: 0.09, blue: 0.16))
                .cornerRadius(8)
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(red: 0.15, green: 0.20, blue: 0.30), lineWidth: 1))

                // Recorded Trips History List
                TripHistoryView()
                    .padding(.top, 4)

            }
            .padding(16)
        }
        .background(Color(red: 0.03, green: 0.04, blue: 0.08).ignoresSafeArea()) // Carbon Deep Navy
        .onAppear {
            setupEngineAndAssets()
        }
    }

    private var cardinalSubtext: String {
        let b = ((headingDeg.truncatingRemainder(dividingBy: 360.0)) + 360.0).truncatingRemainder(dividingBy: 360.0)
        let cardinal: String
        switch b {
        case 337.5...360.0, 0.0..<22.5: cardinal = "NORTH"
        case 22.5..<67.5: cardinal = "NORTH-EAST"
        case 67.5..<112.5: cardinal = "EAST"
        case 112.5..<157.5: cardinal = "SOUTH-EAST"
        case 157.5..<202.5: cardinal = "SOUTH"
        case 202.5..<247.5: cardinal = "SOUTH-WEST"
        case 247.5..<292.5: cardinal = "WEST"
        default: cardinal = "NORTH-WEST"
        }
        if abs(currentLeanAngleDeg) > 1.0 {
            return "\(cardinal) | Lean: \(String(format: "%.1f°", currentLeanAngleDeg))"
        }
        return cardinal
    }

    private var roadMatchSubtext: String {
        if let seg = matchedSegmentId {
            return "\(seg) (\(Int(matchConfidence * 100))%)"
        }
        return isRecording ? "Unmatched road" : "Not tracking"
    }

    // MARK: - Subsystem Setup & Actions

    private func setupEngineAndAssets() {
        // 1. Load Road Graph Pack
        if let roadUrl = Bundle.main.url(forResource: "sample_road_pack", withExtension: "json"),
           let roadData = try? Data(contentsOf: roadUrl),
           let pack = try? RoadGraphPack.fromJsonData(roadData) {
            self.roadPack = pack
        }

        // 2. Load Portable ML Model
        if let modelUrl = Bundle.main.url(forResource: "motion_portable", withExtension: "json"),
           let modelData = try? Data(contentsOf: modelUrl),
           let runner = try? PortableTreeRunner.fromJsonData(modelData) {
            self.portableRunner = runner
            let eng = ContinuumLocationEngine(
                portableRunner: runner,
                vehicleProfile: selectedProfile,
                roadGraphPack: self.roadPack
            )
            eng.delegate = DelegateBridge(parent: self)
            self.engine = eng
        }

        // 3. Start BLE Manager
        bleManager.start(listener: BleListenerBridge(parent: self))
    }

    private func startTrip() {
        guard let eng = engine else { return }
        eng.vehicleProfile = selectedProfile
        eng.roadGraphPack = roadPack

        var modelData: Data? = nil
        if let modelUrl = Bundle.main.url(forResource: "motion_portable", withExtension: "json") {
            modelData = try? Data(contentsOf: modelUrl)
        }
        recorder = TripRecorder(profile: selectedProfile, routeCategory: selectedRouteScenario, modelData: modelData)

        eng.start()
        isRecording = true
        statusText = "Recording sensors and GNSS (\(selectedProfile.rawValue), \(selectedRouteScenario))."
    }

    private func stopTrip() {
        engine?.stop()
        recorder?.close()
        recorder = nil
        isRecording = false
        statusText = "Tracking stopped. Trip log saved to Documents."
    }

    private func anchorDemoRoute() {
        if !isRecording {
            startTrip()
        }
        engine?.setAnchorOrigin(lat: 12.8450, lon: 77.6620, bearingDeg: 0.0)
        currentLat = 12.8450
        currentLon = 77.6620
        statusText = "Anchored to Electronic City Tollway. Move phone to dead reckon!"
    }

    private func simulateDrivingStep() {
        if !isRecording {
            startTrip()
        }
        engine?.simulateStep(speedMps: 18.0, yawRateRad: 0.02, dtS: 2.0)
        statusText = "Simulated 2s driving step (+36m forward, 2.3° curvature)"
    }

    private func triggerBleHazard(_ type: String, severity: Double) {
        _ = bleManager.generateTestHazard(hazardType: type, severity: severity, lat: currentLat, lon: currentLon)
        bleStats = bleManager.getRelayStats()
        bleStatusMessage = "Broadcasted \(type) beacon (3s burst)"
    }

    // MARK: - Delegate Bridge Helpers

    fileprivate class DelegateBridge: ContinuumLocationEngineDelegate {
        var parent: ContentView
        init(parent: ContentView) { self.parent = parent }

        func locationEngine(_ engine: ContinuumLocationEngine, didUpdateLocation location: CLLocation, isFallback: Bool, state: FallbackState, matchResult: MapMatchResult?) {
            DispatchQueue.main.async {
                self.parent.currentLat = location.coordinate.latitude
                self.parent.currentLon = location.coordinate.longitude
                self.parent.speedKmh = max(location.speed, 0.0) * 3.6
                self.parent.headingDeg = location.course >= 0 ? location.course : self.parent.headingDeg
                self.parent.accuracyM = location.horizontalAccuracy
                self.parent.currentState = state
                self.parent.isFallbackActive = isFallback
                self.parent.currentLeanAngleDeg = engine.currentLeanAngleDeg
                self.parent.matchedSegmentId = matchResult?.segmentId
                self.parent.matchConfidence = matchResult?.matchConfidence ?? 0.0

                self.parent.recorder?.logPosition(
                    lat: location.coordinate.latitude,
                    lon: location.coordinate.longitude,
                    speedMps: location.speed,
                    bearingDeg: location.course,
                    accuracyM: location.horizontalAccuracy,
                    isFallback: isFallback,
                    state: state,
                    matchResult: matchResult,
                    leanAngleDeg: engine.currentLeanAngleDeg
                )
            }
        }

        func locationEngine(_ engine: ContinuumLocationEngine, didDetectSurfaceAnomaly eventType: String, severity: Double) {
            DispatchQueue.main.async {
                self.parent.statusText = "Anomaly detected: \(eventType) (severity \(String(format: "%.2f", severity)))"
                self.parent.recorder?.logSurface(kind: eventType, severity: severity)
                self.parent.bleManager.broadcastHazard(hazardType: eventType, severity: severity, lat: self.parent.currentLat, lon: self.parent.currentLon)
                self.parent.bleStats = self.parent.bleManager.getRelayStats()
            }
        }

        func locationEngineDidDetectMountShift(_ engine: ContinuumLocationEngine) {
            DispatchQueue.main.async {
                self.parent.statusText = "Mount alignment changed; reposition the phone"
                self.parent.recorder?.logMountShift()
            }
        }

        func locationEngine(_ engine: ContinuumLocationEngine, didUpdateDiagnostics diagnostics: EngineDiagnostics) {
            DispatchQueue.main.async {
                self.parent.infLatencyUs = diagnostics.lastInferenceLatencyUs
                self.parent.avgInfLatencyUs = diagnostics.avgInferenceLatencyUs
                self.parent.estimatedMemoryKb = diagnostics.estimatedMemoryKb
                self.parent.imuSamples = diagnostics.imuSamplesCount
            }
        }
    }

    fileprivate class BleListenerBridge: TrafficReportListener {
        var parent: ContentView
        init(parent: ContentView) { self.parent = parent }

        func onHazardReceived(_ report: TrafficHazardReport) {
            DispatchQueue.main.async {
                self.parent.bleStats = self.parent.bleManager.getRelayStats()
                self.parent.bleStatusMessage = "BLE Alert: \(report.hazardType) received from peer vehicle!"
                self.parent.recorder?.logTraffic(hazard: report.hazardType, severity: report.severity, peerLat: report.latitude, peerLon: report.longitude, vehicleId: report.vehicleId)
            }
        }
    }
}
