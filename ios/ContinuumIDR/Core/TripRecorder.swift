import Foundation
import CryptoKit

/// Thread-safe foreground trip recorder that writes schema 1.0.0 JSON Lines (JSONL) events.
public final class TripRecorder {

    private let fileURL: URL
    private var fileHandle: FileHandle?
    private let queue = DispatchQueue(label: "ai.continuum.idr.recorder", qos: .utility)
    private var eventCount = 0

    public let tripId: String

    public init(profile: VehicleProfile, routeCategory: String, modelData: Data?) {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyyMMdd_HHmmss"
        let stamp = formatter.string(from: Date())
        self.tripId = "continuum_\(stamp)"

        let tripsDir = TripRecorder.getTripsDirectory()
        self.fileURL = tripsDir.appendingPathComponent("\(tripId).jsonl")

        FileManager.default.createFile(atPath: fileURL.path, contents: nil, attributes: nil)
        self.fileHandle = try? FileHandle(forWritingTo: fileURL)

        let modelHash: String
        if let data = modelData {
            let digest = SHA256.hash(data: data)
            modelHash = digest.map { String(format: "%02x", $0) }.joined()
        } else {
            modelHash = "unknown"
        }

        // Line 1: Metadata Header
        writeMetadata(profile: profile, routeCategory: routeCategory, modelHash: modelHash)
    }

    public static func getTripsDirectory() -> URL {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let dir = docs.appendingPathComponent("trips", isDirectory: true)
        if !FileManager.default.fileExists(atPath: dir.path) {
            try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        }
        return dir
    }

    public static func listRecordedTrips() -> [URL] {
        let dir = getTripsDirectory()
        guard let files = try? FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: [.contentModificationDateKey, .fileSizeKey], options: .skipsHiddenFiles) else {
            return []
        }
        return files.filter { $0.pathExtension == "jsonl" }
            .sorted { url1, url2 in
                let d1 = (try? url1.resourceValues(forKeys: [.contentModificationDateKey]))?.contentModificationDate ?? Date.distantPast
                let d2 = (try? url2.resourceValues(forKeys: [.contentModificationDateKey]))?.contentModificationDate ?? Date.distantPast
                return d1 > d2
            }
    }

    private func writeMetadata(profile: VehicleProfile, routeCategory: String, modelHash: String) {
        let dict: [String: Any] = [
            "type": "metadata",
            "wall_time_ms": Int64(Date().timeIntervalSince1970 * 1000),
            "version": "1.0.0",
            "model_hash": modelHash,
            "device_model": "Apple Device",
            "device_manufacturer": "Apple",
            "os_version": "iOS",
            "vehicle_profile": profile.rawValue,
            "route_category": routeCategory,
            "start_time_ms": Int64(Date().timeIntervalSince1970 * 1000)
        ]
        writeRaw(dict)
    }

    public func logPosition(
        lat: Double,
        lon: Double,
        speedMps: Double,
        bearingDeg: Double,
        accuracyM: Double,
        isFallback: Bool,
        state: FallbackState,
        matchResult: MapMatchResult?,
        leanAngleDeg: Double
    ) {
        var dict: [String: Any] = [
            "type": "position",
            "wall_time_ms": Int64(Date().timeIntervalSince1970 * 1000),
            "lat": lat,
            "lon": lon,
            "speed_mps": speedMps,
            "bearing_deg": bearingDeg,
            "accuracy_m": accuracyM,
            "fallback": isFallback,
            "state": state.rawValue,
            "lean_angle_deg": leanAngleDeg
        ]
        if let match = matchResult {
            dict["matched_segment"] = match.segmentId as Any
            dict["match_confidence"] = match.matchConfidence
            dict["is_ambiguous"] = match.isAmbiguous
        }
        writeRaw(dict)
    }

    public func logGnss(lat: Double, lon: Double, speedMps: Double, bearingDeg: Double, accuracyM: Double) {
        let dict: [String: Any] = [
            "type": "gnss",
            "wall_time_ms": Int64(Date().timeIntervalSince1970 * 1000),
            "lat": lat,
            "lon": lon,
            "speed_mps": speedMps,
            "bearing_deg": bearingDeg,
            "accuracy_m": accuracyM,
            "provider": "CoreLocation"
        ]
        writeRaw(dict)
    }

    public func logImu(sensorType: Int, timestampNs: Int64, values: [Double]) {
        let dict: [String: Any] = [
            "type": "imu",
            "wall_time_ms": Int64(Date().timeIntervalSince1970 * 1000),
            "sensor_type": sensorType,
            "timestamp_ns": timestampNs,
            "values": values
        ]
        writeRaw(dict)
    }

    public func logSurface(kind: String, severity: Double) {
        let dict: [String: Any] = [
            "type": "surface",
            "wall_time_ms": Int64(Date().timeIntervalSince1970 * 1000),
            "kind": kind,
            "severity": severity
        ]
        writeRaw(dict)
    }

    public func logMountShift() {
        let dict: [String: Any] = [
            "type": "mount",
            "wall_time_ms": Int64(Date().timeIntervalSince1970 * 1000),
            "event": "tilt_shift_detected"
        ]
        writeRaw(dict)
    }

    public func logTraffic(hazard: String, severity: Double, peerLat: Double, peerLon: Double, vehicleId: String) {
        let dict: [String: Any] = [
            "type": "traffic",
            "wall_time_ms": Int64(Date().timeIntervalSince1970 * 1000),
            "hazard": hazard,
            "severity": severity,
            "peer_lat": peerLat,
            "peer_lon": peerLon,
            "vehicle_id": vehicleId
        ]
        writeRaw(dict)
    }

    public func logDiagnostics(_ diag: EngineDiagnostics) {
        let dict: [String: Any] = [
            "type": "diagnostics",
            "wall_time_ms": Int64(Date().timeIntervalSince1970 * 1000),
            "imu_samples": diag.imuSamplesCount,
            "gnss_fixes": diag.gnssFixesCount,
            "dead_reckon_steps": diag.deadReckonStepsCount,
            "avg_inference_latency_us": diag.avgInferenceLatencyUs,
            "avg_map_match_latency_us": diag.avgMapMatchLatencyUs,
            "estimated_memory_kb": diag.estimatedMemoryKb
        ]
        writeRaw(dict)
    }

    private func writeRaw(_ dict: [String: Any]) {
        queue.async { [weak self] in
            guard let self = self, let handle = self.fileHandle else { return }
            guard let jsonData = try? JSONSerialization.data(withJSONObject: dict, options: []),
                  var lineStr = String(data: jsonData, encoding: .utf8) else { return }
            lineStr.append("\n")
            if let lineData = lineStr.data(using: .utf8) {
                handle.write(lineData)
                self.eventCount += 1
                if self.eventCount % 100 == 0 {
                    try? handle.synchronize()
                }
            }
        }
    }

    public func close() {
        queue.sync {
            try? fileHandle?.synchronize()
            try? fileHandle?.close()
            fileHandle = nil
        }
    }
}
