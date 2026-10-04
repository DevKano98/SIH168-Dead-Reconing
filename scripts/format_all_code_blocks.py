import re

def format_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Format JSON code box
    json_box_old = r'<div class="code-box">\s*<div class="code-header">\s*<span class="lang">JSON</span>.*?<div class="code-content">.*?</div>\s*</div>'
    json_box_new = '''<div class="code-box">
            <div class="code-header">
              <span class="lang">JSON</span>
              <span>motion_portable.json (Schema Excerpt)</span>
              <button class="copy-btn">Copy</button>
            </div>
            <div class="code-content"><pre><code>{
  "manifest": {
    "version": "1.0.0",
    "model_id": "continuum-motion-p0",
    "uncertainty_bins_mps": [0.0, 5.0, 15.0, 25.0],
    "uncertainty_std_mps": [0.35, 0.65, 1.10, 1.85]
  },
  "speed_mean": 12.435,
  "stop_linear_intercept": -0.852,
  "stop_linear_weights": [-0.12, 0.45, -0.08, ...],
  "speed_trees": [
    [
      {"f": 1, "th": 0.452, "l": 1, "r": 2},
      {"v": -1.24},
      {"f": 27, "th": -0.012, "l": 3, "r": 4},
      {"v": 0.85},
      {"v": 2.15}
    ]
  ]
}</code></pre></div>
          </div>'''
    html = re.sub(json_box_old, json_box_new, html, flags=re.DOTALL)

    # 2. Format Binary V2V mesh box
    binary_box_old = r'<div class="code-box">\s*<div class="code-header">\s*<span class="lang">BINARY</span>.*?<div class="code-content">.*?</div>\s*</div>'
    binary_box_new = '''<div class="code-box">
            <div class="code-header">
              <span class="lang">BINARY</span>
              <span>18-Byte Non-Connectable Ad-Hoc Payload Structure</span>
            </div>
            <div class="code-content"><pre><code>[Byte 0-1]:   Magic Header (0xCA 0xFE)
[Byte 2-5]:   Epoch Timestamp (uint32)
[Byte 6-9]:   Latitude Coordinate (int32, scaled x 10^7)
[Byte 10-13]: Longitude Coordinate (int32, scaled x 10^7)
[Byte 14]:    Anomaly Type (0x01: Pothole, 0x02: Speed Breaker, 0x03: GPS Blackout)
[Byte 15]:    Severity Metric (0–255)
[Byte 16-17]: 16-Bit CRC Checksum</code></pre></div>
          </div>'''
    html = re.sub(binary_box_old, binary_box_new, html, flags=re.DOTALL)

    # 3. Format Python box
    python_box_old = r'<div class="code-box">\s*<div class="code-header">\s*<span class="lang">PYTHON</span>.*?<div class="code-content">.*?</div>\s*</div>'
    python_box_new = '''<div class="code-box">
            <div class="code-header">
              <span class="lang">PYTHON</span>
              <span>Python Research Engine Integration</span>
              <button class="copy-btn">Copy</button>
            </div>
            <div class="code-content"><pre><code>from continuum_idr.engine import IDREngine
from continuum_idr.model import MotionModelBundle
from continuum_idr.types import EngineConfig, IMUSample, GNSSFix

# 1. Initialize portable model bundle and engine configuration
model = MotionModelBundle.load("models/motion_p0")
config = EngineConfig(imu_rate_hz=10.0, gnss_timeout_s=2.0)
engine = IDREngine(model, config)

# 2. Feed 10 Hz IMU samples from smartphone or vehicle bus
state = engine.on_imu(IMUSample(
    timestamp_s=1709234812.105,
    accel_mps2=(0.12, 0.45, 9.81),
    gyro_radps=(0.001, 0.002, -0.015)
))

print(f"Tracking: {state.tracking_mode}, Speed: {state.speed_mps:.2f} m/s, Heading: {state.heading_deg:.1f}°")</code></pre></div>
          </div>'''
    html = re.sub(python_box_old, python_box_new, html, flags=re.DOTALL)

    # 4. Format Kotlin box
    kotlin_box_old = r'<div class="code-box" id="android-sdk">\s*<div class="code-header">\s*<span class="lang">KOTLIN</span>.*?<div class="code-content">.*?</div>\s*</div>'
    kotlin_box_new = '''<div class="code-box" id="android-sdk">
            <div class="code-header">
              <span class="lang">KOTLIN</span>
              <span>Android Embedded SDK Integration</span>
              <button class="copy-btn">Copy</button>
            </div>
            <div class="code-content"><pre><code>val continuumEngine = ContinuumLocationEngine(
    context = this,
    portableRunner = PortableTreeRunner.fromJsonString(modelJson),
    vehicleProfile = ContinuumLocationEngine.VehicleProfile.CAR,
    roadGraphPack = roadPack
)

continuumEngine.start(object : ContinuumLocationEngine.LocationUpdateCallback {
    override fun onLocationUpdate(location: Location, isFallback: Boolean, state: FallbackState) {
        // Feeds Google Maps directly via LocationSource or Mock Location Relay
        googleMapLocationListener.onLocationChanged(location)
    }
    override fun onSurfaceAnomaly(eventType: String, severity: Double) {
        Log.i("IDR", "Road anomaly detected: $eventType (severity: $severity)")
    }
    override fun onMountShiftDetected() {
        Log.w("IDR", "Phone mount shifted > 15 degrees; dynamic re-leveling triggered")
    }
})</code></pre></div>
          </div>'''
    html = re.sub(kotlin_box_old, kotlin_box_new, html, flags=re.DOTALL)

    # 5. Format Bash CLI box
    bash_box_old = r'<div class="code-box" id="quickstart">\s*<div class="code-header">\s*<span class="lang">BASH</span>.*?<div class="code-content">.*?</div>\s*</div>'
    bash_box_new = '''<div class="code-box" id="quickstart">
            <div class="code-header">
              <span class="lang">BASH</span>
              <span>Command-Line Interface (CLI)</span>
              <button class="copy-btn">Copy</button>
            </div>
            <div class="code-content"><pre><code># 1. Install Continuum IDR in local editable mode
pip install -e .

# 2. Launch Continuum Studio desktop simulation cockpit on port 8000
python -m continuum_idr.cli studio --host 127.0.0.1 --port 8000

# 3. Evaluate held-out outage episodes across IO-VNBD dataset
python -m continuum_idr.cli evaluate --artifacts artifacts/evaluation

# 4. Audit and validate a recorded field trip from a smartphone
python -m continuum_idr.cli validate-phone-log artifacts/device_validation/trips/trip_01.jsonl</code></pre></div>
          </div>'''
    html = re.sub(bash_box_old, bash_box_new, html, flags=re.DOTALL)

    # 6. Ensure clean visual arrows for Step 2 and Step 3
    step2_old = r'Go to <strong>Settings</strong>.*?tap <strong>Build Number</strong>'
    step2_new = 'Go to <strong>Settings</strong> &rarr; <strong>About Phone</strong> &rarr; tap <strong>Build Number</strong>'
    html = re.sub(step2_old, step2_new, html)

    step3_old = r'Go to <strong>Settings</strong>.*?choose <strong>Continuum IDR</strong>\.'
    step3_new = 'Go to <strong>Settings</strong> &rarr; <strong>System</strong> &rarr; <strong>Developer Options</strong> &rarr; scroll to <strong>"Select mock location app"</strong> &rarr; choose <strong>Continuum IDR</strong>.'
    html = re.sub(step3_old, step3_new, html)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Successfully formatted all code blocks in {filepath}")

format_html('continuum-idr-platform/index.html')
format_html('docs_site/index.html')
