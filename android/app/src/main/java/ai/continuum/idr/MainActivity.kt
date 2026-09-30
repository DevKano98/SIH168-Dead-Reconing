package ai.continuum.idr

import android.Manifest
import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Spinner
import android.widget.TextView
import java.io.File

class MainActivity : Activity() {

    private lateinit var statusText: TextView
    private lateinit var telemetryText: TextView
    private lateinit var diagnosticsText: TextView
    private lateinit var stateBadge: TextView
    private lateinit var profileSpinner: Spinner
    private lateinit var routeSpinner: Spinner
    private lateinit var bleHudText: TextView
    private lateinit var mapView: MapView
    private lateinit var tripsContainer: LinearLayout

    private var selectedProfile = "CAR"
    private var selectedRouteCategory = "Highway Cruise"
    private var isRecording = false
    private var bleTestManager: TrafficBleManager? = null
    private var lastObservedLat = 12.9716
    private var lastObservedLon = 77.5946

    private val statusReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                TrackingService.ACTION_STATUS -> {
                    val status = intent.getStringExtra(TrackingService.EXTRA_STATUS) ?: "Running"
                    statusText.text = status
                }
                TrackingService.ACTION_TELEMETRY -> {
                    val lat = intent.getDoubleExtra("lat", 0.0)
                    val lon = intent.getDoubleExtra("lon", 0.0)
                    lastObservedLat = lat
                    lastObservedLon = lon
                    val speedMps = intent.getFloatExtra("speed_mps", 0f)
                    val speedKmh = speedMps * 3.6f
                    val bearingDeg = intent.getFloatExtra("bearing_deg", 0f)
                    val accuracyM = intent.getFloatExtra("accuracy_m", 0f)
                    val isFallback = intent.getBooleanExtra("is_fallback", false)
                    val state = intent.getStringExtra("state") ?: "GNSS_HEALTHY"
                    val segmentId = intent.getStringExtra("segment_id")
                    val matchConf = intent.getDoubleExtra("match_confidence", 0.0)
                    val leanAngleDeg = intent.getDoubleExtra("lean_angle_deg", 0.0)

                    val infLatencyUs = intent.getLongExtra("inf_latency_us", 0L)
                    val avgInfLatencyUs = intent.getLongExtra("avg_inf_latency_us", 0L)
                    val memKb = intent.getLongExtra("mem_kb", 0L)
                    val imuSamples = intent.getLongExtra("imu_samples", 0L)

                    // Update State Badge
                    stateBadge.text = state
                    when (state) {
                        "GNSS_HEALTHY" -> {
                            stateBadge.setBackgroundColor(Color.parseColor("#059669")) // Green
                            stateBadge.setTextColor(Color.WHITE)
                        }
                        "FALLBACK_ACTIVE" -> {
                            stateBadge.setBackgroundColor(Color.parseColor("#DC2626")) // Red
                            stateBadge.setTextColor(Color.WHITE)
                        }
                        "RECOVERING" -> {
                            stateBadge.setBackgroundColor(Color.parseColor("#D97706")) // Amber
                            stateBadge.setTextColor(Color.WHITE)
                        }
                        else -> {
                            stateBadge.setBackgroundColor(Color.parseColor("#475569"))
                            stateBadge.setTextColor(Color.WHITE)
                        }
                    }

                    // Update Telemetry Text
                    val mapInfo = if (segmentId != null) "Road: $segmentId (${(matchConf * 100).toInt()}%)" else "Road: Unmatched"
                    val leanInfo = if (Math.abs(leanAngleDeg) > 1.0) " | Lean: %.1f°".format(leanAngleDeg) else ""
                    telemetryText.text = "%.1f km/h | %03.0f° | ±%.1fm%s\nLat: %.6f, Lon: %.6f\n%s".format(
                        speedKmh, bearingDeg, accuracyM, leanInfo, lat, lon, mapInfo
                    )

                    diagnosticsText.text = "Inference: %d µs (avg: %d µs) | Heap: ~%d KB | Samples: %d".format(
                        infLatencyUs, avgInfLatencyUs, memKb, imuSamples
                    )

                    // Update Map View
                    mapView.updateVehicle(lat, lon, bearingDeg, accuracyM, isFallback)
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.parseColor("#0B1120")) // Deep Navy
            setPadding(24, 32, 24, 24)
        }

        // Title Header
        val header = TextView(this).apply {
            text = "Continuum IDR — Navigation Fallback"
            textSize = 20f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(0, 0, 0, 16)
        }
        root.addView(header)

        // State Badge
        stateBadge = TextView(this).apply {
            text = "READY"
            textSize = 14f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#94A3B8"))
            setBackgroundColor(Color.parseColor("#1E293B"))
            gravity = Gravity.CENTER
            setPadding(24, 8, 24, 8)
        }
        root.addView(stateBadge)

        // Telemetry readout
        telemetryText = TextView(this).apply {
            text = "Speed: -- km/h | Bearing: --° | ±--m\nLat: --, Lon: --\nRoad: Not tracking"
            textSize = 14f
            setTextColor(Color.parseColor("#E2E8F0"))
            setPadding(16, 16, 16, 8)
            gravity = Gravity.CENTER
        }
        root.addView(telemetryText)

        // Performance Diagnostics readout
        diagnosticsText = TextView(this).apply {
            text = "Inference: 0 µs | Heap: ~0 KB | Samples: 0"
            textSize = 12f
            setTextColor(Color.parseColor("#38BDF8"))
            setPadding(0, 0, 0, 8)
            gravity = Gravity.CENTER
        }
        root.addView(diagnosticsText)

        // Offline Vector Map View
        mapView = MapView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                550
            ).apply { setMargins(0, 8, 0, 16) }
        }
        // Load sample road pack if available
        try {
            assets.open("sample_road_pack.json").use {
                val pack = RoadGraphPack.fromInputStream(it)
                mapView.setRoadPack(pack)
            }
        } catch (e: Exception) {
            // No pack or pack load failed
        }
        root.addView(mapView)

        // Profile Selector Row
        val profileRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, 0, 0, 16)
        }
        val profileLabel = TextView(this).apply {
            text = "Vehicle Profile: "
            setTextColor(Color.WHITE)
            textSize = 14f
        }
        profileSpinner = Spinner(this).apply {
            val profiles = arrayOf("CAR", "MOTORCYCLE", "PARKING", "EXTERNAL_IMU")
            adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, profiles)
            onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
                override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                    selectedProfile = profiles[position]
                }
                override fun onNothingSelected(parent: AdapterView<*>?) {}
            }
        }
        profileRow.addView(profileLabel)
        profileRow.addView(profileSpinner)
        root.addView(profileRow)

        // Route Category Selector Row
        val routeRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, 0, 0, 16)
        }
        val routeLabel = TextView(this).apply {
            text = "Route Category: "
            setTextColor(Color.WHITE)
            textSize = 14f
        }
        routeSpinner = Spinner(this).apply {
            val categories = arrayOf(
                "Highway Cruise",
                "City Arterial",
                "Stop & Go Traffic",
                "Potholes & Patched",
                "Speed Breakers",
                "Underpass / Tunnel",
                "Parking Ramp & Reverse",
                "Motorcycle High Lean",
                "Engine Idle Vibration"
            )
            adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, categories)
            onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
                override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                    selectedRouteCategory = categories[position]
                }
                override fun onNothingSelected(parent: AdapterView<*>?) {}
            }
        }
        routeRow.addView(routeLabel)
        routeRow.addView(routeSpinner)
        root.addView(routeRow)

        // Action Buttons Row (Start / Stop)
        val buttonsRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
        }
        val startBtn = Button(this).apply {
            text = "Start Trip"
            setBackgroundColor(Color.parseColor("#2563EB"))
            setTextColor(Color.WHITE)
            setOnClickListener { startRecording() }
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                setMargins(0, 0, 8, 0)
            }
        }
        val stopBtn = Button(this).apply {
            text = "Stop Trip"
            setBackgroundColor(Color.parseColor("#475569"))
            setTextColor(Color.WHITE)
            setOnClickListener { stopRecording() }
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                setMargins(8, 0, 0, 0)
            }
        }
        buttonsRow.addView(startBtn)
        buttonsRow.addView(stopBtn)
        root.addView(buttonsRow)

        // Status Message
        statusText = TextView(this).apply {
            text = "Ready to record trip"
            textSize = 13f
            setTextColor(Color.parseColor("#94A3B8"))
            setPadding(0, 12, 0, 8)
            gravity = Gravity.CENTER
        }
        root.addView(statusText)

        // BLE V2V Section
        val bleHeader = TextView(this).apply {
            text = "Cooperative V2V Traffic (BLE Mesh)"
            textSize = 14f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#A7F3D0"))
            setPadding(0, 8, 0, 2)
        }
        root.addView(bleHeader)

        val bleNotice = TextView(this).apply {
            text = "Notice: BLE operates within direct ~10-30m local line-of-sight only, not long-range cellular."
            textSize = 11f
            setTextColor(Color.parseColor("#94A3B8"))
            setPadding(0, 0, 0, 6)
        }
        root.addView(bleNotice)

        bleHudText = TextView(this).apply {
            text = "Relay HUD: Sent: 0 | Recv: 0 | Duplicates: 0 | Expired: 0"
            textSize = 12f
            setTextColor(Color.parseColor("#FDE047"))
            setPadding(0, 0, 0, 8)
        }
        root.addView(bleHudText)

        val bleButtonsRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 12)
        }
        val potholeBleBtn = Button(this).apply {
            text = "Trigger Pothole (BLE)"
            textSize = 12f
            setBackgroundColor(Color.parseColor("#0F766E"))
            setTextColor(Color.WHITE)
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                setMargins(0, 0, 4, 0)
            }
            setOnClickListener {
                bleTestManager?.generateTestHazard("POTHOLE", 0.85, lastObservedLat, lastObservedLon)
                updateBleHud()
            }
        }
        val outageBleBtn = Button(this).apply {
            text = "Trigger Outage (BLE)"
            textSize = 12f
            setBackgroundColor(Color.parseColor("#991B1B"))
            setTextColor(Color.WHITE)
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                setMargins(4, 0, 0, 0)
            }
            setOnClickListener {
                bleTestManager?.generateTestHazard("GNSS_OUTAGE", 1.0, lastObservedLat, lastObservedLon)
                updateBleHud()
            }
        }
        bleButtonsRow.addView(potholeBleBtn)
        bleButtonsRow.addView(outageBleBtn)
        root.addView(bleButtonsRow)

        // Initialize BLE test manager
        bleTestManager = TrafficBleManager(this)
        bleTestManager?.start(object : TrafficBleManager.TrafficReportListener {
            override fun onHazardReceived(report: TrafficHazardReport) {
                runOnUiThread {
                    updateBleHud()
                    statusText.text = "BLE Hazard: ${report.hazardType} at %.4f, %.4f".format(report.latitude, report.longitude)
                }
            }
        })

        // Trip History Header & List Container
        val tripsHeader = TextView(this).apply {
            text = "Recorded Trips (JSONL):"
            textSize = 14f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.WHITE)
            setPadding(0, 8, 0, 8)
        }
        root.addView(tripsHeader)

        tripsContainer = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }
        val scroll = ScrollView(this).apply {
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f)
            addView(tripsContainer)
        }
        root.addView(scroll)

        setContentView(root)
        refreshTripsList()
    }

    override fun onStart() {
        super.onStart()
        val filter = IntentFilter().apply {
            addAction(TrackingService.ACTION_STATUS)
            addAction(TrackingService.ACTION_TELEMETRY)
        }
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(statusReceiver, filter, RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("UnspecifiedRegisterReceiverFlag")
            registerReceiver(statusReceiver, filter)
        }
        refreshTripsList()
    }

    override fun onStop() {
        unregisterReceiver(statusReceiver)
        super.onStop()
    }

    private fun startRecording() {
        val permissions = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
        if (Build.VERSION.SDK_INT >= 33) {
            permissions += Manifest.permission.POST_NOTIFICATIONS
        }
        if (Build.VERSION.SDK_INT >= 31) {
            permissions += Manifest.permission.BLUETOOTH_SCAN
            permissions += Manifest.permission.BLUETOOTH_ADVERTISE
            permissions += Manifest.permission.BLUETOOTH_CONNECT
        }

        val missing = permissions.filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
        if (missing.isNotEmpty()) {
            requestPermissions(missing.toTypedArray(), 10)
            return
        }

        val serviceIntent = Intent(this, TrackingService::class.java).apply {
            putExtra(TrackingService.EXTRA_PROFILE, selectedProfile)
            putExtra(TrackingService.EXTRA_ROUTE_CATEGORY, selectedRouteCategory)
        }
        startForegroundService(serviceIntent)
        isRecording = true
        statusText.text = "Starting tracking service ($selectedProfile profile, $selectedRouteCategory)..."
    }

    private fun stopRecording() {
        stopService(Intent(this, TrackingService::class.java))
        isRecording = false
        statusText.text = "Tracking stopped. Trip saved."
        refreshTripsList()
    }

    private fun refreshTripsList() {
        tripsContainer.removeAllViews()
        val directory = File(getExternalFilesDir(null), "trips")
        if (!directory.exists()) return

        val files = directory.listFiles { _, name -> name.endsWith(".jsonl") }
            ?.sortedByDescending { it.lastModified() }
            ?: return

        if (files.isEmpty()) {
            val emptyView = TextView(this).apply {
                text = "No recorded trips yet."
                setTextColor(Color.parseColor("#64748B"))
                textSize = 12f
            }
            tripsContainer.addView(emptyView)
            return
        }

        for (file in files.take(5)) {
            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setPadding(0, 4, 0, 4)
            }
            val sizeKb = file.length() / 1024
            val nameView = TextView(this).apply {
                text = "${file.name} (${sizeKb} KB)"
                setTextColor(Color.parseColor("#94A3B8"))
                textSize = 12f
                layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
            }
            val shareBtn = Button(this).apply {
                text = "Export"
                textSize = 11f
                setBackgroundColor(Color.parseColor("#334155"))
                setTextColor(Color.WHITE)
                setOnClickListener { shareTripFile(file) }
            }
            row.addView(nameView)
            row.addView(shareBtn)
            tripsContainer.addView(row)
        }
    }

    private fun shareTripFile(file: File) {
        val content = try {
            file.readLines().take(200).joinToString("\n")
        } catch (e: Exception) {
            "Error reading file: ${e.message}"
        }
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_SUBJECT, "Continuum IDR Trip Log: ${file.name}")
            putExtra(Intent.EXTRA_TEXT, content)
        }
        startActivity(Intent.createChooser(intent, "Export Trip Log"))
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        results: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, results)
        if (requestCode == 10 && results.isNotEmpty() && results.all { it == PackageManager.PERMISSION_GRANTED }) {
            startRecording()
        } else {
            statusText.text = "Required permissions not granted"
        }
    }

    private fun updateBleHud() {
        val s = bleTestManager?.getRelayStats() ?: return
        bleHudText.text = "Relay HUD: Sent: ${s.sentCount} | Recv: ${s.receivedCount} | Duplicates: ${s.duplicateCount} | Expired: ${s.expiredCount}"
    }

    override fun onDestroy() {
        bleTestManager?.stop()
        bleTestManager = null
        super.onDestroy()
    }
}

