package ai.continuum.idr

import android.Manifest
import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    private lateinit var status: TextView
    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            status.text = intent.getStringExtra(TrackingService.EXTRA_STATUS) ?: "Recording"
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        status = TextView(this).apply { text = "Ready to record a trip"; textSize = 20f; setPadding(40, 60, 40, 30) }
        val start = Button(this).apply { text = "Start trip recording"; setOnClickListener { startRecording() } }
        val stop = Button(this).apply { text = "Stop recording"; setOnClickListener { stopService(Intent(this@MainActivity, TrackingService::class.java)) } }
        setContentView(LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; addView(status); addView(start); addView(stop) })
    }

    override fun onStart() {
        super.onStart()
        val filter = IntentFilter(TrackingService.ACTION_STATUS)
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(receiver, filter, RECEIVER_NOT_EXPORTED)
        else @Suppress("UnspecifiedRegisterReceiverFlag") registerReceiver(receiver, filter)
    }
    override fun onStop() { unregisterReceiver(receiver); super.onStop() }

    private fun startRecording() {
        val permissions = mutableListOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
        if (Build.VERSION.SDK_INT >= 33) permissions += Manifest.permission.POST_NOTIFICATIONS
        if (permissions.any { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }) {
            requestPermissions(permissions.toTypedArray(), 10)
            return
        }
        startForegroundService(Intent(this, TrackingService::class.java))
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, results: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, results)
        if (requestCode == 10 && results.isNotEmpty() && results.all { it == PackageManager.PERMISSION_GRANTED }) startRecording()
        else status.text = "Location permission is required to record a trip"
    }
}
