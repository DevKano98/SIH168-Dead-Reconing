import re

def clean_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Replace the old 5-stage pipeline diagram block
    old_pipeline_pattern = r'<div class="card" style="margin-top: 1\.5rem;">\s*<h3 class="card-title"[^>]*>Complete 5-Stage Data Transmission Pipeline</h3>\s*<div style="background-color: var\(--bg-subtle\)[^>]*>.*?</div>\s*</div>'
    
    new_pipeline_html = '''<div class="card" style="margin-top: 1.5rem;">
            <h3 class="card-title" style="margin-bottom: 1.25rem;">Complete 5-Stage Data Transmission Pipeline</h3>
            <div class="pipeline-container">
              <!-- Stage 1 -->
              <div class="pipeline-step">
                <div class="pipeline-step-badge">1</div>
                <div class="pipeline-step-content">
                  <div class="pipeline-step-header">
                    <h4 class="pipeline-step-title">Raw Phone IMU Ingestion &amp; Dynamic Leveling</h4>
                    <span class="pipeline-step-tag">100 Hz &rarr; 10 Hz Decimation</span>
                  </div>
                  <p class="pipeline-step-desc">
                    Polls smartphone 6-DoF accelerometer and gyroscope via background HandlerThread. Decimates to a clean 10 Hz buffer. Exponential low-pass filter isolates the 9.81 m/s&sup2; gravity vector from vehicle acceleration; auto-recalibrates if cradle shifts &Delta;&psi; &gt; 15&deg;.
                  </p>
                  <div class="pipeline-step-details">
                    <span class="pipeline-detail-chip">Filter: <b>g</b><sub>k</sub> = 0.98 <b>g</b><sub>k&minus;1</sub> + 0.02 <b>a</b><sub>raw,k</sub></span>
                    <span class="pipeline-detail-chip">Cutoff: f<sub>c</sub> &approx; 0.32 Hz</span>
                    <span class="pipeline-detail-chip">Mount Shift Guard: &Delta;&psi; &gt; 15&deg;</span>
                  </div>
                </div>
              </div>

              <div class="pipeline-connector">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
              </div>

              <!-- Stage 2 -->
              <div class="pipeline-step">
                <div class="pipeline-step-badge">2</div>
                <div class="pipeline-step-content">
                  <div class="pipeline-step-header">
                    <h4 class="pipeline-step-title">Causal Feature Extraction</h4>
                    <span class="pipeline-step-tag">2.0s Sliding Window Buffer</span>
                  </div>
                  <p class="pipeline-step-desc">
                    Computes 42 statistical moments across 6 channels (<i>a</i><sub>x</sub>, <i>a</i><sub>y</sub>, <i>a</i><sub>z</sub>, <i>&omega;</i><sub>x</sub>, <i>&omega;</i><sub>y</sub>, <i>&omega;</i><sub>z</sub>) over 20 causal samples. Eliminates high-frequency vibration noise while capturing braking and acceleration onset.
                  </p>
                  <div class="pipeline-step-details">
                    <span class="pipeline-detail-chip">Moments: Mean, Std, Min, Max, Last, Delta, Root-Energy</span>
                    <span class="pipeline-detail-chip">Output: FloatArray(42)</span>
                  </div>
                </div>
              </div>

              <div class="pipeline-connector">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
              </div>

              <!-- Stage 3 -->
              <div class="pipeline-step">
                <div class="pipeline-step-badge">3</div>
                <div class="pipeline-step-content">
                  <div class="pipeline-step-header">
                    <h4 class="pipeline-step-title">Dual Edge Machine Learning Inference</h4>
                    <span class="pipeline-step-tag">85&ndash;140 &micro;s &bull; &lt;4.5 MB RAM</span>
                  </div>
                  <p class="pipeline-step-desc">
                    Zero-dependency Kotlin tree runner (<code>PortableTreeRunner.kt</code>). Speed regressor estimates velocity (0&ndash;55 m/s); stop detector evaluates P(stopped) to activate Zero-Velocity Updates (ZUPT) and clamp speed to 0.0 m/s when stopped.
                  </p>
                  <div class="pipeline-step-details">
                    <span class="pipeline-detail-chip">Speed: HistGradientBoosting (50&ndash;100 trees)</span>
                    <span class="pipeline-detail-chip">Stop Gate: Logistic Regression (P &ge; 0.50 &rarr; 0.0 m/s)</span>
                  </div>
                </div>
              </div>

              <div class="pipeline-connector">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
              </div>

              <!-- Stage 4 -->
              <div class="pipeline-step">
                <div class="pipeline-step-badge">4</div>
                <div class="pipeline-step-content">
                  <div class="pipeline-step-header">
                    <h4 class="pipeline-step-title">Kinematics, Lean Decoupling &amp; Road Snapping</h4>
                    <span class="pipeline-step-tag">WGS-84 Flat-Earth</span>
                  </div>
                  <p class="pipeline-step-desc">
                    Integrates gyro heading with two-wheeler roll-lean angle decoupling. Projects coordinates onto local tangent plane. Soft centerline pull (85% IMU / 15% road) eliminates lateral wander; broadcasts 18-byte ad-hoc BLE hazard alerts.
                  </p>
                  <div class="pipeline-step-details">
                    <span class="pipeline-detail-chip">Lean Decoupling: &theta;<sub>lean</sub> = arctan(v&middot;&omega; / g)</span>
                    <span class="pipeline-detail-chip">Map Pull: 85% Inertial / 15% Road</span>
                    <span class="pipeline-detail-chip">V2V: 18-Byte BLE Mesh</span>
                  </div>
                </div>
              </div>

              <div class="pipeline-connector">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
              </div>

              <!-- Stage 5 -->
              <div class="pipeline-step">
                <div class="pipeline-step-badge">5</div>
                <div class="pipeline-step-content">
                  <div class="pipeline-step-header">
                    <h4 class="pipeline-step-title">Android OS Relay &amp; Smooth Re-Convergence</h4>
                    <span class="pipeline-step-tag">LocationManager Hook</span>
                  </div>
                  <p class="pipeline-step-desc">
                    <code>SystemMockRelay.kt</code> injects synthetic coordinates into Android's <code>GPS_PROVIDER</code>, powering unmodified Google Maps continuously during blackouts. On tunnel exit, a 2.5s linear blending window prevents visual jumping.
                  </p>
                  <div class="pipeline-step-details">
                    <span class="pipeline-detail-chip">Consumer Apps: Google Maps, Waze, Uber</span>
                    <span class="pipeline-detail-chip">Recovery: <b>p</b><sub>blend</sub> = (1 &minus; &alpha;)<b>p</b><sub>idr</sub> + &alpha;<b>p</b><sub>gnss</sub> (2.5s)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>'''
    
    html = re.sub(old_pipeline_pattern, new_pipeline_html, html, flags=re.DOTALL)

    # 2. Replace raw math in Sensors & Kinematics
    old_kinematics_math = r'<div class="math-block">\s*<div class="math-title">1\. Dynamic Exponential Gravity Leveling Filter</div>.*?</div>\s*<p class="text-xs text-ink-secondary"[^>]*>.*?</p>\s*<div class="math-block">\s*<div class="math-title">2\. Heading Integration & Two-Wheeler Lean Decoupling</div>.*?</div>\s*<p class="text-xs text-ink-secondary"[^>]*>.*?</p>\s*<div class="math-block">\s*<div class="math-title">3\. Planar WGS-84 Flat-Earth Projection</div>.*?</div>'

    new_kinematics_math = '''<div class="formula-card">
            <div class="formula-title">1. Dynamic Exponential Gravity Leveling Filter</div>
            <div class="formula-line">
              <b>g</b><sub>k</sub> = 0.98 <b>g</b><sub>k&minus;1</sub> + 0.02 <b>a</b><sub>raw, k</sub>
              &nbsp;&nbsp;<span class="formula-note">(f<sub>c</sub> &approx; 0.32 Hz)</span>
            </div>
            <div class="formula-line">
              <b>a</b><sub>linear, k</sub> = <b>a</b><sub>raw, k</sub> &minus; <b>g</b><sub>k</sub>
            </div>
          </div>
          <p class="text-xs text-ink-secondary" style="margin-bottom: 1rem;">
            This isolates the constant 9.81 m/s&sup2; downward gravity vector from true vehicle acceleration. If a bump or phone nudge causes tilt deviation &Delta;&psi; &gt; 15&deg;, an alignment supervisor automatically re-calibrates the vehicle forward axis.
          </p>

          <div class="formula-card">
            <div class="formula-title">2. Heading Integration &amp; Two-Wheeler Lean Decoupling</div>
            <div class="formula-line">
              &theta;<sub>k</sub> = (&theta;<sub>k&minus;1</sub> + &omega;<sub>z,true</sub> &middot; &Delta;t) mod 360&deg;
            </div>
            <div class="formula-line">
              &theta;<sub>lean</sub> = arctan((v &middot; &omega;<sub>z</sub>) / g) &nbsp;&nbsp;&implies;&nbsp;&nbsp; &omega;<sub>z,true</sub> = &omega;<sub>z</sub> &middot; cos(&theta;<sub>lean</sub>)
            </div>
          </div>
          <p class="text-xs text-ink-secondary" style="margin-bottom: 1rem;">
            On motorcycles and scooters, cornering produces roll-lean angles up to 35&deg;. Without lean decoupling, the phone's gyroscope registers massive false heading distortion. The cosine projection normalizes angular velocity onto the true vertical yaw axis.
          </p>

          <div class="formula-card">
            <div class="formula-title">3. Planar WGS-84 Flat-Earth Projection</div>
            <div class="formula-line">
              &Delta;N = v &middot; &Delta;t &middot; cos(&theta;) , &nbsp;&nbsp;&nbsp;&Delta;E = v &middot; &Delta;t &middot; sin(&theta;)
            </div>
            <div class="formula-line">
              lat<sub>k</sub> = lat<sub>k&minus;1</sub> + &Delta;N / R<sub>E</sub> , &nbsp;&nbsp;&nbsp;lon<sub>k</sub> = lon<sub>k&minus;1</sub> + &Delta;E / (R<sub>E</sub> &middot; cos(lat<sub>k&minus;1</sub>))
            </div>
          </div>'''

    html = re.sub(old_kinematics_math, new_kinematics_math, html, flags=re.DOTALL)

    # 3. Replace Reconvergence equation
    old_reconv = r'<div class="math-block" id="reconvergence">\s*<div class="math-title">Smooth 2\.5-Second Linear Re-Convergence Filter</div>.*?</div>'
    new_reconv = '''<div class="formula-card" id="reconvergence">
            <div class="formula-title">Smooth 2.5-Second Linear Re-Convergence Filter</div>
            <div class="formula-line">
              <b>p</b><sub>blend</sub>(t) = (1 &minus; &alpha;(t)) <b>p</b><sub>idr</sub>(t) + &alpha;(t) <b>p</b><sub>gnss</sub>(t)
              &nbsp;&nbsp;<span class="formula-note">&alpha;(t) = (t &minus; t<sub>exit</sub>) / 2.5s</span>
            </div>
          </div>'''
    html = re.sub(old_reconv, new_reconv, html, flags=re.DOTALL)

    # 4. Replace Road Snapping equation
    old_snapping = r'<div class="math-block">\s*<div class="math-title">Soft Centerline Pull & Heading Damping \(Confidence ≥ 70%\)</div>.*?</div>'
    new_snapping = '''<div class="formula-card">
            <div class="formula-title">Soft Centerline Pull &amp; Heading Damping (Confidence &ge; 70%)</div>
            <div class="formula-line">
              <b>p</b><sub>corrected</sub> = 0.85 <b>p</b><sub>inertial</sub> + 0.15 <b>p</b><sub>centerline</sub>
            </div>
            <div class="formula-line">
              &theta;<sub>corrected</sub> = 0.96 &theta;<sub>gyro</sub> + 0.04 &theta;<sub>road</sub>
            </div>
          </div>'''
    html = re.sub(old_snapping, new_snapping, html, flags=re.DOTALL)

    # 5. Clean up individual inline math strings across the document
    replacements = [
        # Table lines
        (r'Valid GNSS fixes arriving \(\$\\Delta t \\le 1\.0\\text\{s\}\$\)', 'Valid GNSS fixes arriving (&Delta;t &le; 1.0s)'),
        (r'Satellite fix delayed \(\$1\.0\\text\{s\} &lt; \\Delta t \\le 2\.0\\text\{s\}\$\)', 'Satellite fix delayed (1.0s &lt; &Delta;t &le; 2.0s)'),
        (r'Fixes absent for \$\\Delta t &gt; 2\.0\\text\{s\}\$ \(Tunnel entry\)', 'Fixes absent for &Delta;t &gt; 2.0s (Tunnel entry)'),
        (r'Linear Accel \$a_x\$', 'Linear Accel <i>a</i><sub>x</sub>'),
        (r'Linear Accel \$a_y\$', 'Linear Accel <i>a</i><sub>y</sub>'),
        (r'Linear Accel \$a_z\$', 'Linear Accel <i>a</i><sub>z</sub>'),
        (r'Gyroscope \$\\omega_x\$', 'Gyroscope <i>&omega;</i><sub>x</sub>'),
        (r'Gyroscope \$\\omega_y\$', 'Gyroscope <i>&omega;</i><sub>y</sub>'),
        (r'Gyroscope \$\\omega_z\$', 'Gyroscope <i>&omega;</i><sub>z</sub>'),
        (r'\(\$x_\\text\{last\} - x_\\text\{first\}\$\)', '(x<sub>last</sub> &minus; x<sub>first</sub>)'),
        (r'\(\$\\sqrt\{\\frac\{1\}\{N\}\\sum x\^2\}\$\)', '(&radic;(1/N &sum; x&sup2;))'),
        (r'\$\\eta = 0\.1\$', '&eta; = 0.1'),
        (r'P\(stopped\) \\ge 0\.50', 'P(stopped) &ge; 0.50'),
        (r'<strong>\$0\.0\\text\{ m/s\}\$</strong>', '<strong>0.0 m/s</strong>'),
        (r'<strong>\$\|\\hat\{v\}_\\text\{Py\} - \\hat\{v\}_\\text\{Kt\}\| &lt; 10\^\{-5\}\\text\{ m/s\}\$</strong>', '<strong>|v&#770;<sub>Py</sub> &minus; v&#770;<sub>Kt</sub>| &lt; 10<sup>&minus;5</sup> m/s</strong>'),
        (r'\(f_c \\approx 0\.32\\text\{ Hz\}\)', '(f<sub>c</sub> &approx; 0.32 Hz)'),
        (r'\$\\Delta\\psi > 15\^\\circ\$', '&Delta;&psi; &gt; 15&deg;'),
        (r'\(\$a_z &lt; -4\.0\\text\{ m/s\}\^2\$\)', '(<i>a</i><sub>z</sub> &lt; &minus;4.0 m/s&sup2;)'),
        (r'\(\$a_z &gt; 4\.5\\text\{ m/s\}\^2\$\)', '(<i>a</i><sub>z</sub> &gt; +4.5 m/s&sup2;)'),
        (r'\(\$\\theta = \\arctan\(v\\omega / g\)\$\)', '(&theta; = arctan(v&middot;&omega; / g))'),
        (r'\$0\.5\^\\circ - 2\.0\^\\circ/\\text\{s\}\$', '0.5&deg; &minus; 2.0&deg;/s'),
        (r'gyro \$\\omega_z\$', 'gyro <i>&omega;</i><sub>z</sub>'),
        (r'90 road turns', '90&deg; road turns'),
        (r'90° road turns', '90&deg; road turns'),
        (r'\$0\^\\circ / 360\^\\circ\$', '0&deg; / 360&deg;'),
        (r'\$\\pm 4\.5\\text\{ m/s\}\^2\$', '&plusmn;4.5 m/s&sup2;'),
        (r'\$a_z\$', '<i>a</i><sub>z</sub>'),
        (r'100 Hz \$\\to\$ 10 Hz', '100 Hz &rarr; 10 Hz'),
        (r'Settings \$\\to\$ About Phone', 'Settings &rarr; About Phone'),
        (r'About Phone \$\\to\$ tap', 'About Phone &rarr; tap'),
        (r'Settings \$\\to\$ System', 'Settings &rarr; System'),
        (r'System \$\\to\$ Developer Options', 'System &rarr; Developer Options'),
        (r'Developer Options \$\\to\$ scroll', 'Developer Options &rarr; scroll'),
        (r'mock location app" \$\\to\$ choose', 'mock location app" &rarr; choose'),
        (r'\$10,000\+', '$10,000+'),
        (r'Log\.i\("IDR", "Road anomaly detected: \$eventType \(severity: \$severity\)"\)', 'Log.i("IDR", "Road anomaly detected: $eventType (severity: $severity)")'),
    ]

    for pattern, repl in replacements:
        html = re.sub(pattern, repl, html)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Successfully cleaned {filepath}')

clean_html('continuum-idr-platform/index.html')
clean_html('docs_site/index.html')
