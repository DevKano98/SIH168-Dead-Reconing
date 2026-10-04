import SwiftUI

public struct TripHistoryView: View {
    @State private var trips: [URL] = []
    @State private var selectedTripForShare: URL? = nil
    @State private var showingShareSheet = false

    public init() {}

    public var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("RECORDED TRIPS (JSONL)")
                    .font(.system(size: 9, weight: .bold))
                    .foregroundColor(Color(red: 0.39, green: 0.45, blue: 0.55))
                    .tracking(0.5)

                Spacer()

                Button {
                    refreshTrips()
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(Color(red: 0.22, green: 0.74, blue: 0.97))
                }
            }

            if trips.isEmpty {
                Text("No recorded trips yet. Tap 'START TRIP' to capture telemetry.")
                    .font(.system(size: 11))
                    .foregroundColor(.gray)
                    .padding(.vertical, 8)
            } else {
                ForEach(trips.prefix(5), id: \.self) { trip in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(trip.lastPathComponent)
                                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                .foregroundColor(.white)
                            Text(fileSizeString(for: trip))
                                .font(.system(size: 10))
                                .foregroundColor(.gray)
                        }

                        Spacer()

                        Button("Export") {
                            selectedTripForShare = trip
                            showingShareSheet = true
                        }
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(Color(red: 0.22, green: 0.74, blue: 0.97))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color(red: 0.12, green: 0.16, blue: 0.24))
                        .cornerRadius(6)
                    }
                    .padding(10)
                    .background(Color(red: 0.06, green: 0.09, blue: 0.16))
                    .cornerRadius(8)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color(red: 0.15, green: 0.20, blue: 0.30), lineWidth: 1)
                    )
                }
            }
        }
        .onAppear {
            refreshTrips()
        }
        .sheet(isPresented: $showingShareSheet) {
            if let url = selectedTripForShare {
                ActivityViewController(activityItems: [url])
            }
        }
    }

    private func refreshTrips() {
        trips = TripRecorder.listRecordedTrips()
    }

    private func fileSizeString(for url: URL) -> String {
        guard let attrs = try? FileManager.default.attributesOfItem(atPath: url.path),
              let size = attrs[.size] as? Int64 else {
            return "0 KB"
        }
        return "\(size / 1024) KB"
    }
}

struct ActivityViewController: UIViewControllerRepresentable {
    var activityItems: [Any]
    var applicationActivities: [UIActivity]? = nil

    func makeUIViewController(context: UIViewControllerRepresentableContext<ActivityViewController>) -> UIActivityViewController {
        let controller = UIActivityViewController(activityItems: activityItems, applicationActivities: applicationActivities)
        return controller
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: UIViewControllerRepresentableContext<ActivityViewController>) {}
}
