# Continuum IDR — Standalone Documentation & Showcase Platform

A completely self-contained, zero-dependency documentation portal and asset host for **Continuum IDR** (Smart India Hackathon SIH 2026).

---

## 🚀 How to Run

### Option 1: Just Double-Click! (No Setup Needed)
Simply open **`index.html`** in this folder by double-clicking it in Windows File Explorer.
* It will open directly in Google Chrome, Microsoft Edge, Mozilla Firefox, or Safari.
* Zero build step, zero npm install, zero terminal commands required.
* All video demos, benchmark graphs, documentation, and the Android APK download button work immediately via `file://`.

### Option 2: Host on the Web (GitHub Pages / Netlify / Vercel / S3)
Because this project contains only static HTML, CSS, JavaScript, and pre-packaged assets:
1. **GitHub Pages:** Push this folder to a GitHub repository and turn on GitHub Pages in repository settings.
2. **Netlify / Vercel:** Drag and drop this folder directly into the Netlify/Vercel dashboard.
3. **Local HTTP Server (Optional):**
   ```bash
   python -m http.server 8080
   ```

---

## 📁 Standalone Project Structure

```
continuum-idr-platform/
├── index.html                   # Complete documentation portal with interactive navigation
├── styles.css                   # Professional white engineering theme stylesheet
├── app.js                       # Interactive search, code copying, lightbox, and scroll-spy
├── README.md                    # Project documentation & hosting instructions
└── assets/
    ├── apk/
    │   └── Continuum_IDR_v1.0.apk         # Compiled production Android APK (1.1 MB)
    ├── videos/
    │   ├── dashboard_recording.mp4        # Desktop Studio simulation screen recording (22.2 MB)
    │   └── mobile_recording.mp4           # Android mobile app screen recording (6.0 MB)
    └── images/
        ├── trajectory.png                 # Planar trajectory line plot
        ├── error_vs_time.png              # Horizontal error accumulation vs outage duration
        ├── speed_profile.png              # ML predicted velocity vs ground truth speed
        ├── heading_and_yaw.png            # Gyro yaw integration and compass heading
        ├── map_matching_snapping.png      # Topological road snapping vectors
        ├── surface_shocks_and_imu.png     # Vertical az shock spikes and anomaly flags
        └── benchmark_distributions.png    # Aggregate benchmark error distribution
```

---

## 📱 Features Included
* **Top Header & Hero APK Download Button:** Directly downloads `Continuum_IDR_v1.0.apk` (1.1 MB).
* **Two Native Video Players:** High-definition screen recordings of the Desktop Studio simulation and Android Mobile App.
* **Seven Scientific Benchmark Graphs:** High-resolution empirical line plots with interactive click-to-zoom Lightbox and deep engineering explanations.
* **Complete System Documentation:** Dynamic gravity leveling, 42-moment causal ML extractor, `HistGradientBoosting` speed model, ZUPT stop classifier, Android OS Mock GPS Relay, Indian road shock filtering, and V2V BLE mesh protocol.
* **Interactive UI:** Live search filtering, one-click code snippet copying, and responsive layout.
