// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ContinuumIDR",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .library(
            name: "ContinuumIDRCore",
            targets: ["ContinuumIDRCore"]
        )
    ],
    dependencies: [],
    targets: [
        .target(
            name: "ContinuumIDRCore",
            path: "ContinuumIDR",
            exclude: [
                "App",
                "Resources/Info.plist"
            ],
            resources: [
                .process("Resources/motion_portable.json"),
                .process("Resources/sample_road_pack.json"),
                .process("Resources/parity_fixture.json"),
                .process("Resources/Assets.xcassets")
            ]
        ),
        .testTarget(
            name: "ContinuumIDRTests",
            dependencies: ["ContinuumIDRCore"],
            path: "ContinuumIDRTests",
            resources: [
                .process("../ContinuumIDR/Resources/motion_portable.json"),
                .process("../ContinuumIDR/Resources/sample_road_pack.json"),
                .process("../ContinuumIDR/Resources/parity_fixture.json")
            ]
        )
    ]
)
