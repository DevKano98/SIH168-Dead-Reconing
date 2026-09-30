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

    // Metric Displays
    private lateinit var speedValueText: TextView
    private lateinit var headingValueText: TextView
    private lateinit var headingSubText: TextView
    private lateinit var accuracyValueText: TextView
    private lateinit var roadMatchSubText: TextView

    // Status & Diagnostics
    private lateinit var stateBadge: TextView
    private lateinit var statusText: TextView
    private lateinit var diagnosticsText: TextView
    private lateinit var mockRelayStatusText: TextView

    // Controls & Selectors
    private lateinit var startBtn: Button
    private lateinit var stopBtn: Button
    private lateinit var anchorBtn: Button
    private lateinit var mockRelayToggleBtn: Button
    private lateinit var profileSpinner: Spinner
    private lateinit var routeSpinner: Spinner
    private lateinit var bleHudText: TextView
    private lateinit var mapView: MapView
    private lateinit var tripsContainer: LinearLayout

    private var selectedProfile = "CAR"
    private var selectedRouteCategory = "Highway Cruise"
    private var isRecording = false
    private var isMockRelayActive = false
    private var bleTestManager: TrafficBleManager? = null
    private var lastObservedLat = 12.8450
    private var lastObservedLon = 77.6620

    private fun Int.dp(): Int = (this * resources.displayMetrics.density).toInt()

    private val statusReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                TrackingService.ACTION_STATUS -> {
                    val status = intent.getStringExtra(TrackingService.EXTRA_STATUS) ?: "Running"
                    statusText.text = status
                }
                TrackingService.ACTION_HEARTBEAT -> {
                    val imuSamples = intent.getLongExtra("imu_samples", 0L)
                    val memKb = intent.getLongExtra("mem_kb", 0L)
                    val infLatencyUs = intent.getLongExtra("inf_latency_us", 0L)
                    val avgInfLatencyUs = intent.getLongExtra("avg_inf_latency_us", 0L)
                    val hasOrigin = intent.getBooleanExtra("has_origin", false)

                    diagnosticsText.text = "Inference: %d µs (avg %d µs) • Heap: ~%d KB • IMU: %d samples".format(
                        infLatencyUs, avgInfLatencyUs, memKb, imuSamples
                    )

                    if (!hasOrigin && isRecording) {
                        stateBadge.text = "● WAITING FOR GNSS LOCK (INDOOR)"
                        stateBadge.setBackgroundColor(Color.parseColor("#D97706")) // Amber
                        statusText.text = "Sensors active (%d samples). Acquiring satellites or tap 'Anchor Demo'.".format(imuSamples)
                    }
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

                    // Update Cockpit Bento Hero Cards
                    speedValueText.text = "%.1f".format(speedKmh)
                    headingValueText.text = "%03.0f°".format(bearingDeg)

                    val cardinal = getCardinalDirection(bearingDeg)
                    val leanStr = if (Math.abs(leanAngleDeg) > 1.0) " | Lean: %.1f°".format(leanAngleDeg) else ""
                    headingSubText.text = "$cardinal$leanStr"

                    accuracyValueText.text = "±%.1fm".format(accuracyM)
                    roadMatchSubText.text = if (segmentId != null) "$segmentId (${(matchConf * 100).toInt()}%)" else "Unmatched road"

                    // Update State Badge Ribbon
                    when (state) {
                        "GNSS_HEALTHY" -> {
                            stateBadge.text = "● GNSS LOCKED (ACTIVE)"
                            stateBadge.setBackgroundColor(Color.parseColor("#059669")) // Emerald Green
                        }
                        "FALLBACK_ACTIVE" -> {
                            stateBadge.text = "● INERTIAL DEAD RECKONING (FALLBACK ACTIVE)"
                            stateBadge.setBackgroundColor(Color.parseColor("#DC2626")) // Crimson Red
                        }
                        "RECOVERING" -> {
                            stateBadge.text = "● RE-CONVERGING GNSS"
                            stateBadge.setBackgroundColor(Color.parseColor("#D97706")) // Amber
                        }
                        else -> {
                            stateBadge.text = "● $state"
                            stateBadge.setBackgroundColor(Color.parseColor("#334155"))
                        }
                    }

                    diagnosticsText.text = "Inference: %d µs (avg %d µs) • Heap: ~%d KB • IMU: %d samples".format(
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
            setBackgroundColor(Color.parseColor("#070B14")) // Carbon Deep Navy
            setPadding(16.dp(), 20.dp(), 16.dp(), 24.dp())
        }

        // Top Header
        val brandRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, 0, 0, 4.dp())
        }
        val appTitle = TextView(this).apply {
            text = "CONTINUUM"
            textSize = 20f
            setTypeface(Typeface.create("sans-serif-black", Typeface.BOLD))
            setTextColor(Color.WHITE)
        }
        val appBadge = TextView(this).apply {
            text = " IDR "
            textSize = 12f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#38BDF8"))
            setBackgroundColor(Color.parseColor("#0F2942"))
            setPadding(6.dp(), 2.dp(), 6.dp(), 2.dp())
        }
        val appSub = TextView(this).apply {
            text = " • SATELLITE FALLBACK SYSTEM"
            textSize = 11f
            setTextColor(Color.parseColor("#64748B"))
        }
        brandRow.addView(appTitle)
        brandRow.addView(appBadge)
        brandRow.addView(appSub)
        root.addView(brandRow)

        // System State Ribbon (Pill Badge)
        stateBadge = TextView(this).apply {
            text = "● READY FOR TRIP"
            textSize = 12f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.WHITE)
            setBackgroundResource(R.drawable.bg_pill)
            gravity = Gravity.CENTER
            setPadding(16.dp(), 8.dp(), 16.dp(), 8.dp())
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, 8.dp(), 0, 12.dp())
            }
        }
        root.addView(stateBadge)

        // Automotive Instrument Bento Cluster (3 Hero Cards)
        val clusterRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, 0, 0, 12.dp())
            }
        }

        // Card 1: Speedometer
        val speedCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundResource(R.drawable.bg_card)
            setPadding(12.dp(), 12.dp(), 12.dp(), 12.dp())
            gravity = Gravity.CENTER
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.1f).apply {
                setMargins(0, 0, 6.dp(), 0)
            }
        }
        val speedLabel = TextView(this).apply {
            text = "ESTIMATED SPEED"
            textSize = 9f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#64748B"))
        }
        speedValueText = TextView(this).apply {
            text = "--"
            textSize = 28f
            setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD))
            setTextColor(Color.parseColor("#38BDF8")) // Cyan Accent
        }
        val speedUnit = TextView(this).apply {
            text = "KM / H"
            textSize = 10f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#94A3B8"))
        }
        speedCard.addView(speedLabel)
        speedCard.addView(speedValueText)
        speedCard.addView(speedUnit)
        clusterRow.addView(speedCard)

        // Card 2: Compass & Bearing
        val headingCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundResource(R.drawable.bg_card)
            setPadding(12.dp(), 12.dp(), 12.dp(), 12.dp())
            gravity = Gravity.CENTER
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                setMargins(3.dp(), 0, 3.dp(), 0)
            }
        }
        val headingLabel = TextView(this).apply {
            text = "HEADING"
            textSize = 9f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#64748B"))
        }
        headingValueText = TextView(this).apply {
            text = "---°"
            textSize = 28f
            setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD))
            setTextColor(Color.WHITE)
        }
        headingSubText = TextView(this).apply {
            text = "NORTH"
            textSize = 10f
            setTextColor(Color.parseColor("#94A3B8"))
        }
        headingCard.addView(headingLabel)
        headingCard.addView(headingValueText)
        headingCard.addView(headingSubText)
        clusterRow.addView(headingCard)

        // Card 3: Precision & Road Match
        val precisionCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundResource(R.drawable.bg_card)
            setPadding(12.dp(), 12.dp(), 12.dp(), 12.dp())
            gravity = Gravity.CENTER
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.1f).apply {
                setMargins(6.dp(), 0, 0, 0)
            }
        }
        val precisionLabel = TextView(this).apply {
            text = "UNCERTAINTY"
            textSize = 9f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#64748B"))
        }
        accuracyValueText = TextView(this).apply {
            text = "±--m"
            textSize = 24f
            setTypeface(Typeface.create("sans-serif-condensed", Typeface.BOLD))
            setTextColor(Color.parseColor("#10B981")) // Emerald
        }
        roadMatchSubText = TextView(this).apply {
            text = "Not tracking"
            textSize = 9f
            setTextColor(Color.parseColor("#94A3B8"))
            maxLines = 1
        }
        precisionCard.addView(precisionLabel)
        precisionCard.addView(accuracyValueText)
        precisionCard.addView(roadMatchSubText)
        clusterRow.addView(precisionCard)

        root.addView(clusterRow)

        // Map View in Card Frame
        val mapCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundResource(R.drawable.bg_card)
            setPadding(10.dp(), 10.dp(), 10.dp(), 10.dp())
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, 0, 0, 12.dp())
            }
        }
        mapView = MapView(this).apply {
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 240.dp())
        }
        try {
            assets.open("sample_road_pack.json").use {
                val pack = RoadGraphPack.fromInputStream(it)
                mapView.setRoadPack(pack)
            }
        } catch (e: Exception) {}
        mapCard.addView(mapView)

        // Map Control Bar (Recenter / Indoor Anchor)
        val mapActionsRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, 8.dp(), 0, 0)
        }
        anchorBtn = Button(this).apply {
            text = "Anchor to Demo Route (Indoor Test)"
            textSize = 12f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.WHITE)
            setBackgroundResource(R.drawable.btn_teal)
            layoutParams = LinearLayout.LayoutParams(0, 40.dp(), 1f).apply {
                setMargins(0, 0, 4.dp(), 0)
            }
            setOnClickListener {
                if (!isRecording) startRecording()
                val anchorIntent = Intent(this@MainActivity, TrackingService::class.java).apply {
                    action = TrackingService.ACTION_SET_ANCHOR
                    putExtra("lat", 12.8450)
                    putExtra("lon", 77.6620)
                    putExtra("bearing_deg", 0.0f)
                }
                startService(anchorIntent)
                statusText.text = "Anchored to Electronic City Tollway. Move/shake phone to dead reckon!"
            }
        }
        val recenterBtn = Button(this).apply {
            text = "Recenter"
            textSize = 12f
            setTextColor(Color.WHITE)
            setBackgroundResource(R.drawable.btn_secondary)
            layoutParams = LinearLayout.LayoutParams(0, 40.dp(), 0.5f).apply {
                setMargins(4.dp(), 0, 0, 0)
            }
            setOnClickListener {
                mapView.setAutoFollow(true)
            }
        }
        mapActionsRow.addView(anchorBtn)
        mapActionsRow.addView(recenterBtn)
        mapCard.addView(mapActionsRow)
        root.addView(mapCard)

        // Google Maps & External Navigation Relay Card (NEW)
        val relayCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundResource(R.drawable.bg_card)
            setPadding(14.dp(), 12.dp(), 14.dp(), 12.dp())
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, 0, 0, 12.dp())
            }
        }
        val relayHeaderRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val relayTitle = TextView(this).apply {
            text = "GOOGLE MAPS & NAVIGATION RELAY"
            textSize = 11f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#38BDF8"))
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        }
        mockRelayToggleBtn = Button(this).apply {
            text = "ENABLE MOCK GPS"
            textSize = 10f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.WHITE)
            setBackgroundResource(R.drawable.btn_primary)
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, 36.dp())
            setOnClickListener { toggleMockRelay() }
        }
        relayHeaderRow.addView(relayTitle)
        relayHeaderRow.addView(mockRelayToggleBtn)
        relayCard.addView(relayHeaderRow)

        mockRelayStatusText = TextView(this).apply {
            text = "Status: Disabled. Tap button to feed real-time fallback coordinates to Google Maps & Waze during tunnels."
            textSize = 11f
            setTextColor(Color.parseColor("#94A3B8"))
            setPadding(0, 6.dp(), 0, 0)
        }
        relayCard.addView(mockRelayStatusText)
        root.addView(relayCard)

        // Vehicle Profile & Route Setup Card
        val configCard = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setBackgroundResource(R.drawable.bg_card)
            setPadding(12.dp(), 10.dp(), 12.dp(), 10.dp())
            gravity = Gravity.CENTER_VERTICAL
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, 0, 0, 12.dp())
            }
        }
        val profileCol = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                setMargins(0, 0, 6.dp(), 0)
            }
        }
        val profileLabel = TextView(this).apply {
            text = "VEHICLE PROFILE"
            textSize = 9f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#64748B"))
        }
        profileSpinner = Spinner(this).apply {
            setBackgroundResource(R.drawable.spinner_bg)
            val profiles = arrayOf("CAR", "MOTORCYCLE", "PARKING", "EXTERNAL_IMU")
            adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, profiles)
            onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
                override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                    selectedProfile = profiles[position]
                    (view as? TextView)?.setTextColor(Color.WHITE)
                }
                override fun onNothingSelected(parent: AdapterView<*>?) {}
            }
        }
        profileCol.addView(profileLabel)
        profileCol.addView(profileSpinner)

        val routeCol = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                setMargins(6.dp(), 0, 0, 0)
            }
        }
        val routeLabel = TextView(this).apply {
            text = "ROUTE SCENARIO"
            textSize = 9f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#64748B"))
        }
        routeSpinner = Spinner(this).apply {
            setBackgroundResource(R.drawable.spinner_bg)
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
                    (view as? TextView)?.setTextColor(Color.WHITE)
                }
                override fun onNothingSelected(parent: AdapterView<*>?) {}
            }
        }
        routeCol.addView(routeLabel)
        routeCol.addView(routeSpinner)
        configCard.addView(profileCol)
        configCard.addView(routeCol)
        root.addView(configCard)

        // Action Deck (Start Trip / Stop Trip)
        val buttonsRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, 0, 0, 8.dp())
            }
        }
        startBtn = Button(this).apply {
            text = "START TRIP"
            textSize = 14f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.WHITE)
            setBackgroundResource(R.drawable.btn_primary)
            setOnClickListener { startRecording() }
            layoutParams = LinearLayout.LayoutParams(0, 50.dp(), 1.2f).apply {
                setMargins(0, 0, 8.dp(), 0)
            }
        }
        stopBtn = Button(this).apply {
            text = "STOP TRIP"
            textSize = 14f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#94A3B8"))
            setBackgroundResource(R.drawable.btn_secondary)
            isEnabled = false
            setOnClickListener { stopRecording() }
            layoutParams = LinearLayout.LayoutParams(0, 50.dp(), 1f)
        }
        buttonsRow.addView(startBtn)
        buttonsRow.addView(stopBtn)
        root.addView(buttonsRow)

        // Status Message Bar
        statusText = TextView(this).apply {
            text = "Ready to record trip"
            textSize = 12f
            setTextColor(Color.parseColor("#94A3B8"))
            gravity = Gravity.CENTER
            setPadding(0, 4.dp(), 0, 8.dp())
        }
        root.addView(statusText)

        // Diagnostics HUD Card
        val diagCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundResource(R.drawable.bg_card)
            setPadding(12.dp(), 10.dp(), 12.dp(), 10.dp())
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, 0, 0, 12.dp())
            }
        }
        val diagLabel = TextView(this).apply {
            text = "SYSTEM & INFERENCE TELEMETRY"
            textSize = 9f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#64748B"))
        }
        diagnosticsText = TextView(this).apply {
            text = "Inference: 0 µs (avg 0 µs) • Heap: ~0 KB • IMU: 0 samples"
            textSize = 11f
            setTextColor(Color.parseColor("#38BDF8"))
            setPadding(0, 4.dp(), 0, 0)
        }
        diagCard.addView(diagLabel)
        diagCard.addView(diagnosticsText)
        root.addView(diagCard)

        // V2V Mesh Card
        val bleCard = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundResource(R.drawable.bg_card)
            setPadding(12.dp(), 10.dp(), 12.dp(), 10.dp())
            layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                setMargins(0, 0, 0, 12.dp())
            }
        }
        val bleTitle = TextView(this).apply {
            text = "COOPERATIVE V2V TRAFFIC (BLE DIRECT 10–30M)"
            textSize = 9f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#64748B"))
        }
        bleHudText = TextView(this).apply {
            text = "Relay HUD: Sent: 0 | Recv: 0 | Duplicates: 0"
            textSize = 11f
            setTextColor(Color.parseColor("#FDE047"))
            setPadding(0, 2.dp(), 0, 6.dp())
        }
        val bleBtnsRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
        }
        val potholeBleBtn = Button(this).apply {
            text = "Trigger Pothole"
            textSize = 11f
            setTextColor(Color.WHITE)
            setBackgroundResource(R.drawable.btn_teal)
            layoutParams = LinearLayout.LayoutParams(0, 36.dp(), 1f).apply { setMargins(0, 0, 4.dp(), 0) }
            setOnClickListener {
                bleTestManager?.generateTestHazard("POTHOLE", 0.85, lastObservedLat, lastObservedLon)
                updateBleHud()
            }
        }
        val outageBleBtn = Button(this).apply {
            text = "Trigger Outage"
            textSize = 11f
            setTextColor(Color.WHITE)
            setBackgroundResource(R.drawable.btn_danger)
            layoutParams = LinearLayout.LayoutParams(0, 36.dp(), 1f).apply { setMargins(4.dp(), 0, 0, 0) }
            setOnClickListener {
                bleTestManager?.generateTestHazard("GNSS_OUTAGE", 1.0, lastObservedLat, lastObservedLon)
                updateBleHud()
            }
        }
        bleBtnsRow.addView(potholeBleBtn)
        bleBtnsRow.addView(outageBleBtn)
        bleCard.addView(bleTitle)
        bleCard.addView(bleHudText)
        bleCard.addView(bleBtnsRow)
        root.addView(bleCard)

        // Trip History Header & List Container
        val tripsHeader = TextView(this).apply {
            text = "RECORDED TRIPS (JSONL)"
            textSize = 9f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.parseColor("#64748B"))
            setPadding(0, 4.dp(), 0, 6.dp())
        }
        root.addView(tripsHeader)

        tripsContainer = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
        }
        root.addView(tripsContainer)

        // Scrollable Shell
        val scroll = ScrollView(this).apply {
            layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
            addView(root)
        }
        setContentView(scroll)

        // Initialize BLE test manager
        bleTestManager = TrafficBleManager(this)
        bleTestManager?.start(object : TrafficBleManager.TrafficReportListener {
            override fun onHazardReceived(report: TrafficHazardReport) {
                runOnUiThread {
                    updateBleHud()
                    statusText.text = "BLE Alert: ${report.hazardType} ahead!"
                }
            }
        })

        refreshTripsList()
    }

    override fun onStart() {
        super.onStart()
        val filter = IntentFilter().apply {
            addAction(TrackingService.ACTION_STATUS)
            addAction(TrackingService.ACTION_TELEMETRY)
            addAction(TrackingService.ACTION_HEARTBEAT)
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

    private fun toggleMockRelay() {
        isMockRelayActive = !isMockRelayActive
        if (isMockRelayActive) {
            mockRelayToggleBtn.text = "STOP RELAY"
            mockRelayToggleBtn.setBackgroundResource(R.drawable.btn_danger)
            mockRelayStatusText.text = "Status: Relay ACTIVE. Pushing dead-reckoning directly to Android GPS (Google Maps connected)."
            mockRelayStatusText.setTextColor(Color.parseColor("#34D399")) // Green
        } else {
            mockRelayToggleBtn.text = "ENABLE MOCK GPS"
            mockRelayToggleBtn.setBackgroundResource(R.drawable.btn_primary)
            mockRelayStatusText.text = "Status: Disabled. Tap button to feed fallback coordinates to Google Maps & Waze."
            mockRelayStatusText.setTextColor(Color.parseColor("#94A3B8"))
        }

        if (isRecording) {
            val intent = Intent(this, TrackingService::class.java).apply {
                action = TrackingService.ACTION_TOGGLE_MOCK_RELAY
                putExtra("enable", isMockRelayActive)
            }
            startService(intent)
        }
    }

    private fun startRecording() {
        val requiredPermissions = mutableListOf(
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
        if (Build.VERSION.SDK_INT >= 33) {
            requiredPermissions += Manifest.permission.POST_NOTIFICATIONS
        }

        val missingRequired = requiredPermissions.filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
        if (missingRequired.isNotEmpty()) {
            val allToRequest = missingRequired.toMutableList()
            if (Build.VERSION.SDK_INT >= 31) {
                if (checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) allToRequest += Manifest.permission.BLUETOOTH_SCAN
                if (checkSelfPermission(Manifest.permission.BLUETOOTH_ADVERTISE) != PackageManager.PERMISSION_GRANTED) allToRequest += Manifest.permission.BLUETOOTH_ADVERTISE
                if (checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) allToRequest += Manifest.permission.BLUETOOTH_CONNECT
            }
            requestPermissions(allToRequest.toTypedArray(), 10)
            return
        }

        val serviceIntent = Intent(this, TrackingService::class.java).apply {
            putExtra(TrackingService.EXTRA_PROFILE, selectedProfile)
            putExtra(TrackingService.EXTRA_ROUTE_CATEGORY, selectedRouteCategory)
        }
        startForegroundService(serviceIntent)
        isRecording = true
        startBtn.text = "RECORDING..."
        startBtn.isEnabled = false
        startBtn.setBackgroundResource(R.drawable.btn_secondary)
        startBtn.setTextColor(Color.parseColor("#34D399")) // Emerald
        stopBtn.isEnabled = true
        stopBtn.setBackgroundResource(R.drawable.btn_danger)
        stopBtn.setTextColor(Color.WHITE)
        stateBadge.text = "● INITIALIZING NAVIGATION ENGINE..."
        stateBadge.setBackgroundColor(Color.parseColor("#2563EB"))
        statusText.text = "Starting tracking service ($selectedProfile, $selectedRouteCategory)..."
    }

    private fun stopRecording() {
        stopService(Intent(this, TrackingService::class.java))
        isRecording = false
        startBtn.text = "START TRIP"
        startBtn.isEnabled = true
        startBtn.setBackgroundResource(R.drawable.btn_primary)
        startBtn.setTextColor(Color.WHITE)
        stopBtn.isEnabled = false
        stopBtn.setBackgroundResource(R.drawable.btn_secondary)
        stopBtn.setTextColor(Color.parseColor("#94A3B8"))
        stateBadge.text = "● READY FOR TRIP"
        stateBadge.setBackgroundResource(R.drawable.bg_pill)
        statusText.text = "Tracking stopped. Trip log saved."
        refreshTripsList()
    }

    private fun getCardinalDirection(bearingDeg: Float): String {
        val b = ((bearingDeg % 360f) + 360f) % 360f
        return when {
            b >= 337.5 || b < 22.5 -> "NORTH"
            b < 67.5 -> "NORTH-EAST"
            b < 112.5 -> "EAST"
            b < 157.5 -> "SOUTH-EAST"
            b < 202.5 -> "SOUTH"
            b < 247.5 -> "SOUTH-WEST"
            b < 292.5 -> "WEST"
            else -> "NORTH-WEST"
        }
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
                setPadding(0, 4.dp(), 0, 4.dp())
            }
            tripsContainer.addView(emptyView)
            return
        }

        for (file in files.take(5)) {
            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
                setBackgroundResource(R.drawable.bg_card)
                setPadding(12.dp(), 8.dp(), 12.dp(), 8.dp())
                layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply {
                    setMargins(0, 0, 0, 6.dp())
                }
            }
            val sizeKb = file.length() / 1024
            val nameView = TextView(this).apply {
                text = "${file.name}\n${sizeKb} KB"
                setTextColor(Color.parseColor("#94A3B8"))
                textSize = 11f
                layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
            }
            val shareBtn = Button(this).apply {
                text = "Export"
                textSize = 11f
                setTextColor(Color.WHITE)
                setBackgroundResource(R.drawable.btn_secondary)
                layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, 36.dp())
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
        if (requestCode == 10) {
            val hasFine = checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
            val hasCoarse = checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
            if (hasFine || hasCoarse) {
                startRecording()
            } else {
                statusText.text = "Location permission is required for Continuum IDR"
            }
        }
    }

    private fun updateBleHud() {
        val s = bleTestManager?.getRelayStats() ?: return
        bleHudText.text = "Relay HUD: Sent: ${s.sentCount} | Recv: ${s.receivedCount} | Duplicates: ${s.duplicateCount}"
    }

    override fun onDestroy() {
        bleTestManager?.stop()
        bleTestManager = null
        super.onDestroy()
    }
}
