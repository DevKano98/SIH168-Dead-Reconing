plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "ai.continuum.idr"
    compileSdk = 35

    defaultConfig {
        applicationId = "ai.continuum.idr"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20231013")
}

val copyModelAsset = tasks.register<Copy>("copyModelAsset") {
    from("../../models/portable/motion_portable.json")
    into("src/main/assets")
}

tasks.named("preBuild") {
    dependsOn(copyModelAsset)
}
