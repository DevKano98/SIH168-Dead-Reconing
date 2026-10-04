import SwiftUI

public struct BentoMetricCard: View {
    let title: String
    let value: String
    let unitOrSub: String
    let accentColor: Color
    var subColor: Color = Color(red: 0.58, green: 0.64, blue: 0.72) // Slate 400

    public init(
        title: String,
        value: String,
        unitOrSub: String,
        accentColor: Color,
        subColor: Color = Color(red: 0.58, green: 0.64, blue: 0.72)
    ) {
        self.title = title
        self.value = value
        self.unitOrSub = unitOrSub
        self.accentColor = accentColor
        self.subColor = subColor
    }

    public var body: some View {
        VStack(spacing: 4) {
            Text(title.uppercased())
                .font(.system(size: 9, weight: .bold))
                .foregroundColor(Color(red: 0.39, green: 0.45, blue: 0.55))
                .tracking(0.5)

            Text(value)
                .font(.system(size: 26, weight: .bold, design: .rounded))
                .foregroundColor(accentColor)
                .lineLimit(1)
                .minimumScaleFactor(0.7)

            Text(unitOrSub)
                .font(.system(size: 10, weight: .semibold))
                .foregroundColor(subColor)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 12)
        .padding(.horizontal, 8)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(red: 0.06, green: 0.09, blue: 0.16)) // Carbon Navy Card
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color(red: 0.15, green: 0.20, blue: 0.30), lineWidth: 1)
                )
        )
    }
}
