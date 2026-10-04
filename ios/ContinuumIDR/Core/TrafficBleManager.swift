import Foundation
import CoreBluetooth

public protocol TrafficReportListener: AnyObject {
    func onHazardReceived(_ report: TrafficHazardReport)
}

/// Localized Vehicle-to-Vehicle (V2V) cooperative hazard sharing
/// over Bluetooth Low Energy (BLE) using CoreBluetooth.
public final class TrafficBleManager: NSObject, CBCentralManagerDelegate, CBPeripheralManagerDelegate {

    public weak var listener: TrafficReportListener?

    private var centralManager: CBCentralManager?
    private var peripheralManager: CBPeripheralManager?

    private var isAdvertising = false
    private var isScanning = false

    private var sentCount: Int64 = 0
    private var receivedCount: Int64 = 0
    private var relayedCount: Int64 = 0
    private var duplicateCount: Int64 = 0
    private var expiredCount: Int64 = 0

    private var recentHazards: [String: TimeInterval] = [:]

    private let continuumManufacturerId: UInt16 = 0x0C1D
    private let serviceUuid = CBUUID(string: "0000C1D0-0000-1000-8000-00805F9B34FB")

    public override init() {
        super.init()
    }

    public func start(listener: TrafficReportListener) {
        self.listener = listener
        centralManager = CBCentralManager(delegate: self, queue: .main)
        peripheralManager = CBPeripheralManager(delegate: self, queue: .main)
    }

    public func stop() {
        stopAdvertising()
        stopScanning()
        listener = nil
    }

    public func getRelayStats() -> BleRelayStats {
        return BleRelayStats(
            sentCount: sentCount,
            receivedCount: receivedCount,
            relayedCount: relayedCount,
            duplicateCount: duplicateCount,
            expiredCount: expiredCount
        )
    }

    public func resetStats() {
        sentCount = 0
        receivedCount = 0
        relayedCount = 0
        duplicateCount = 0
        expiredCount = 0
        recentHazards.removeAll()
    }

    // MARK: - Central (Scanning)

    private func startScanning() {
        guard let central = centralManager, central.state == .poweredOn, !isScanning else { return }
        central.scanForPeripherals(
            withServices: nil, // Allow manufacturer data match
            options: [CBCentralManagerScanOptionAllowDuplicatesKey: true]
        )
        isScanning = true
    }

    private func stopScanning() {
        if isScanning {
            centralManager?.stopScan()
            isScanning = false
        }
    }

    public func centralManagerDidUpdateState(_ central: CBCentralManager) {
        if central.state == .poweredOn {
            startScanning()
        } else {
            isScanning = false
        }
    }

    public func centralManager(
        _ central: CBCentralManager,
        didDiscover peripheral: CBPeripheral,
        advertisementData: [String: Any],
        rssi RSSI: NSNumber
    ) {
        guard let mfgData = advertisementData[CBAdvertisementDataManufacturerDataKey] as? Data else {
            return
        }
        guard mfgData.count >= 20 else { // 2 bytes Company ID + 18 bytes payload
            return
        }

        let companyId = mfgData.withUnsafeBytes { $0.load(as: UInt16.self) }
        guard companyId == continuumManufacturerId else { return }

        let payload = mfgData.subdata(in: 2..<20)
        guard let report = parseHazardPayload(payload) else { return }

        receivedCount += 1
        let now = Date().timeIntervalSince1970
        let key = "\(report.hazardType)_\(Int(report.latitude * 1000))_\(Int(report.longitude * 1000))"

        if let lastSeen = recentHazards[key] {
            if now - lastSeen < 30.0 {
                duplicateCount += 1
                return
            }
            if now - lastSeen >= 60.0 {
                expiredCount += 1
            }
        }

        recentHazards[key] = now
        listener?.onHazardReceived(report)
    }

    // MARK: - Peripheral (Advertising)

    public func peripheralManagerDidUpdateState(_ peripheral: CBPeripheralManager) {
        if peripheral.state != .poweredOn {
            isAdvertising = false
        }
    }

    public func broadcastHazard(hazardType: String, severity: Double, lat: Double, lon: Double) {
        sentCount += 1
        guard let peripheral = peripheralManager, peripheral.state == .poweredOn else { return }

        let typeByte: UInt8
        switch hazardType {
        case "GNSS_OUTAGE": typeByte = 1
        case "SPEED_BREAKER": typeByte = 2
        case "POTHOLE": typeByte = 3
        case "TRAFFIC_JAM": typeByte = 4
        default: typeByte = 0
        }

        let sevByte = UInt8(min(max(severity, 0.0), 1.0) * 100.0)

        var data = Data()
        var compId = continuumManufacturerId
        data.append(Data(bytes: &compId, count: 2))
        data.append(typeByte)
        data.append(sevByte)

        var latBE = lat.bitPattern.bigEndian
        var lonBE = lon.bitPattern.bigEndian
        data.append(Data(bytes: &latBE, count: 8))
        data.append(Data(bytes: &lonBE, count: 8))

        let adData: [String: Any] = [
            CBAdvertisementDataManufacturerDataKey: data,
            CBAdvertisementDataServiceUUIDsKey: [serviceUuid]
        ]

        if isAdvertising {
            peripheral.stopAdvertising()
        }

        peripheral.startAdvertising(adData)
        isAdvertising = true

        // Stop advertising after 3-second burst
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) { [weak self] in
            self?.stopAdvertising()
        }
    }

    private func stopAdvertising() {
        if isAdvertising {
            peripheralManager?.stopAdvertising()
            isAdvertising = false
        }
    }

    public func generateTestHazard(hazardType: String, severity: Double, lat: Double, lon: Double) -> TrafficHazardReport {
        broadcastHazard(hazardType: hazardType, severity: severity, lat: lat, lon: lon)
        let report = TrafficHazardReport(
            hazardType: hazardType,
            severity: severity,
            latitude: lat,
            longitude: lon,
            timestampMs: Int64(Date().timeIntervalSince1970 * 1000),
            vehicleId: "simulated_local_node"
        )
        listener?.onHazardReceived(report)
        return report
    }

    private func parseHazardPayload(_ data: Data) -> TrafficHazardReport? {
        guard data.count >= 18 else { return nil }

        let typeByte = data[0]
        let hazard: String
        switch typeByte {
        case 1: hazard = "GNSS_OUTAGE"
        case 2: hazard = "SPEED_BREAKER"
        case 3: hazard = "POTHOLE"
        case 4: hazard = "TRAFFIC_JAM"
        default: hazard = "UNKNOWN"
        }

        let sev = Double(data[1]) / 100.0

        let latBits = data.subdata(in: 2..<10).withUnsafeBytes { $0.load(as: UInt64.self).bigEndian }
        let lonBits = data.subdata(in: 10..<18).withUnsafeBytes { $0.load(as: UInt64.self).bigEndian }

        let lat = Double(bitPattern: latBits)
        let lon = Double(bitPattern: lonBits)

        guard lat.isFinite && lon.isFinite else { return nil }

        return TrafficHazardReport(
            hazardType: hazard,
            severity: sev,
            latitude: lat,
            longitude: lon,
            timestampMs: Int64(Date().timeIntervalSince1970 * 1000),
            vehicleId: "peer_ble"
        )
    }
}
