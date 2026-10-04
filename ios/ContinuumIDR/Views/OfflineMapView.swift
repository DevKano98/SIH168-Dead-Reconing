import SwiftUI

public struct OfflineMapView: View {
    public var roadPack: RoadGraphPack?
    public var vehicleLat: Double?
    public var vehicleLon: Double?
    public var vehicleHeadingDeg: Double
    public var vehicleUncertaintyM: Double
    public var isFallbackActive: Bool

    @State private var scale: CGFloat = 2.0 // pixels per meter
    @State private var centerEastM: Double = 0.0
    @State private var centerNorthM: Double = 0.0
    @State private var autoFollow: Bool = true
    @State private var breadcrumbs: [(lat: Double, lon: Double)] = []

    // Drag / Pan State
    @State private var lastDragOffset: CGSize = .zero

    public init(
        roadPack: RoadGraphPack?,
        vehicleLat: Double?,
        vehicleLon: Double?,
        vehicleHeadingDeg: Double = 0.0,
        vehicleUncertaintyM: Double = 5.0,
        isFallbackActive: Bool = false
    ) {
        self.roadPack = roadPack
        self.vehicleLat = vehicleLat
        self.vehicleLon = vehicleLon
        self.vehicleHeadingDeg = vehicleHeadingDeg
        self.vehicleUncertaintyM = vehicleUncertaintyM
        self.isFallbackActive = isFallbackActive
    }

    public var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .bottomTrailing) {
                // Background & Vector Canvas
                Canvas { context, size in
                    let midX = size.width / 2.0
                    let midY = size.height / 2.0

                    // Fill background
                    context.fill(Path(CGRect(origin: .zero, size: size)), with: .color(Color(red: 0.06, green: 0.09, blue: 0.16)))

                    guard let pack = roadPack else {
                        // Placeholder text
                        let text = Text("No offline road pack loaded")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.gray)
                        context.draw(text, at: CGPoint(x: midX, y: midY))
                        return
                    }

                    // 1. Draw Road Segments
                    for seg in pack.segments.values {
                        let sx = midX + CGFloat((seg.startEastM - centerEastM) * Double(scale))
                        let sy = midY - CGFloat((seg.startNorthM - centerNorthM) * Double(scale))
                        let ex = midX + CGFloat((seg.endEastM - centerEastM) * Double(scale))
                        let ey = midY - CGFloat((seg.endNorthM - centerNorthM) * Double(scale))

                        var path = Path()
                        path.move(to: CGPoint(x: sx, y: sy))
                        path.addLine(to: CGPoint(x: ex, y: ey))

                        let roadColor: Color
                        let lineWidth: CGFloat
                        switch seg.roadType {
                        case "motorway":
                            roadColor = Color(red: 0.22, green: 0.74, blue: 0.97) // Sky 400
                            lineWidth = 5
                        case "service":
                            roadColor = Color(red: 0.28, green: 0.33, blue: 0.41) // Slate 600
                            lineWidth = 2.5
                        default:
                            roadColor = Color(red: 0.58, green: 0.64, blue: 0.72) // Slate 400
                            lineWidth = 3.5
                        }

                        context.stroke(path, with: .color(roadColor), lineWidth: lineWidth)
                    }

                    // 2. Draw Trajectory Breadcrumbs
                    if breadcrumbs.count >= 2 {
                        var trail = Path()
                        let first = breadcrumbs[0]
                        let (fe, fn) = pack.toEnu(lat: first.lat, lon: first.lon)
                        trail.move(to: CGPoint(
                            x: midX + CGFloat((fe - centerEastM) * Double(scale)),
                            y: midY - CGFloat((fn - centerNorthM) * Double(scale))
                        ))

                        for i in 1..<breadcrumbs.count {
                            let pt = breadcrumbs[i]
                            let (e, n) = pack.toEnu(lat: pt.lat, lon: pt.lon)
                            trail.addLine(to: CGPoint(
                                x: midX + CGFloat((e - centerEastM) * Double(scale)),
                                y: midY - CGFloat((n - centerNorthM) * Double(scale))
                            ))
                        }

                        context.stroke(trail, with: .color(Color(red: 0.96, green: 0.62, blue: 0.04)), lineWidth: 3)
                    }

                    // 3. Draw Vehicle
                    if let vLat = vehicleLat, let vLon = vehicleLon {
                        let (ve, vn) = pack.toEnu(lat: vLat, lon: vLon)
                        let vx = midX + CGFloat((ve - centerEastM) * Double(scale))
                        let vy = midY - CGFloat((vn - centerNorthM) * Double(scale))

                        // Uncertainty Ellipse
                        let uncertPx = max(CGFloat(vehicleUncertaintyM * Double(scale)), 8.0)
                        let circleRect = CGRect(x: vx - uncertPx, y: vy - uncertPx, width: uncertPx * 2, height: uncertPx * 2)
                        context.fill(Path(ellipseIn: circleRect), with: .color(Color(red: 0.22, green: 0.74, blue: 0.97).opacity(0.18)))
                        context.stroke(Path(ellipseIn: circleRect), with: .color(Color(red: 0.22, green: 0.74, blue: 0.97).opacity(0.6)), lineWidth: 1.5)

                        // Vehicle Directional Cone
                        let headingRad = vehicleHeadingDeg * .pi / 180.0
                        let markerSize: CGFloat = 16.0

                        var cone = Path()
                        let tipX = vx + markerSize * 1.5 * CGFloat(sin(headingRad))
                        let tipY = vy - markerSize * 1.5 * CGFloat(cos(headingRad))
                        let leftX = vx + markerSize * CGFloat(sin(headingRad + 2.5))
                        let leftY = vy - markerSize * CGFloat(cos(headingRad + 2.5))
                        let rightX = vx + markerSize * CGFloat(sin(headingRad - 2.5))
                        let rightY = vy - markerSize * CGFloat(cos(headingRad - 2.5))

                        cone.move(to: CGPoint(x: tipX, y: tipY))
                        cone.addLine(to: CGPoint(x: leftX, y: leftY))
                        cone.addLine(to: CGPoint(x: vx, y: vy))
                        cone.addLine(to: CGPoint(x: rightX, y: rightY))
                        cone.closeSubpath()

                        let vehicleColor = isFallbackActive ? Color(red: 0.94, green: 0.27, blue: 0.27) : Color(red: 0.06, green: 0.73, blue: 0.51)
                        context.fill(cone, with: .color(vehicleColor))
                    }

                    // 4. Draw Dynamic Scale Bar
                    let targetBarMeters = max(min(100.0 / Double(scale), 1000.0), 10.0)
                    let roundedMeters: Int
                    if targetBarMeters < 25 { roundedMeters = 20 }
                    else if targetBarMeters < 75 { roundedMeters = 50 }
                    else if targetBarMeters < 150 { roundedMeters = 100 }
                    else if targetBarMeters < 350 { roundedMeters = 250 }
                    else if targetBarMeters < 750 { roundedMeters = 500 }
                    else { roundedMeters = 1000 }

                    let barWidthPx = CGFloat(Double(roundedMeters) * Double(scale))
                    let barRight = size.width - 24
                    let barLeft = barRight - barWidthPx
                    let barY = size.height - 24

                    var scalePath = Path()
                    scalePath.move(to: CGPoint(x: barLeft, y: barY))
                    scalePath.addLine(to: CGPoint(x: barRight, y: barY))
                    scalePath.move(to: CGPoint(x: barLeft, y: barY - 6))
                    scalePath.addLine(to: CGPoint(x: barLeft, y: barY + 6))
                    scalePath.move(to: CGPoint(x: barRight, y: barY - 6))
                    scalePath.addLine(to: CGPoint(x: barRight, y: barY + 6))
                    context.stroke(scalePath, with: .color(.white), lineWidth: 2)

                    let scaleLabel = Text("\(roundedMeters)m")
                        .font(.system(size: 9, weight: .bold))
                        .foregroundColor(.white)
                    context.draw(scaleLabel, at: CGPoint(x: barLeft + barWidthPx / 2.0, y: barY - 12))
                }
                .gesture(
                    DragGesture()
                        .onChanged { value in
                            autoFollow = false
                            let dx = Double(value.translation.width - lastDragOffset.width) / Double(scale)
                            let dy = Double(value.translation.height - lastDragOffset.height) / Double(scale)
                            centerEastM -= dx
                            centerNorthM += dy
                            lastDragOffset = value.translation
                        }
                        .onEnded { _ in
                            lastDragOffset = .zero
                        }
                )
                .gesture(
                    MagnificationGesture()
                        .onChanged { mag in
                            scale = max(min(scale * mag, 20.0), 0.2)
                        }
                )

                // Top Left Overlay: Map Info Tag
                VStack(alignment: .leading, spacing: 2) {
                    if let pack = roadPack {
                        Text("OFFLINE ROAD PACK: \(pack.name.uppercased())")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundColor(Color(red: 0.22, green: 0.74, blue: 0.97))
                        Text("\(pack.segments.count) Vector Segments Cached")
                            .font(.system(size: 8))
                            .foregroundColor(.gray)
                    }
                }
                .padding(8)
                .background(Color.black.opacity(0.6))
                .cornerRadius(6)
                .padding(10)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)

                // Bottom Right Floating Recenter Button
                Button {
                    autoFollow = true
                    recenterOnVehicle()
                } label: {
                    Image(systemName: autoFollow ? "location.fill" : "location")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(autoFollow ? Color(red: 0.22, green: 0.74, blue: 0.97) : .white)
                        .padding(10)
                        .background(Color(red: 0.12, green: 0.16, blue: 0.24))
                        .clipShape(Circle())
                        .overlay(Circle().stroke(Color.white.opacity(0.2), lineWidth: 1))
                }
                .padding(12)
            }
            .onChange(of: vehicleLat) { _ in
                updateBreadcrumbsAndFollow()
            }
            .onAppear {
                if let pack = roadPack, let first = pack.nodes.values.first {
                    centerEastM = first.eastM
                    centerNorthM = first.northM
                }
            }
        }
        .frame(height: 240)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(red: 0.15, green: 0.20, blue: 0.30), lineWidth: 1)
        )
    }

    private func recenterOnVehicle() {
        guard let vLat = vehicleLat, let vLon = vehicleLon, let pack = roadPack else { return }
        let (ve, vn) = pack.toEnu(lat: vLat, lon: vLon)
        centerEastM = ve
        centerNorthM = vn
    }

    private func updateBreadcrumbsAndFollow() {
        guard let lat = vehicleLat, let lon = vehicleLon else { return }
        breadcrumbs.append((lat: lat, lon: lon))
        if breadcrumbs.count > 500 {
            breadcrumbs.removeFirst()
        }
        if autoFollow, let pack = roadPack {
            let (ve, vn) = pack.toEnu(lat: lat, lon: lon)
            centerEastM = ve
            centerNorthM = vn
        }
    }
}
