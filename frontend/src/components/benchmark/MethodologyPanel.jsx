import React from 'react';
import { Info } from 'lucide-react';

export function MethodologyPanel() {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
      <div className="flex items-center gap-2">
        <Info className="w-4 h-4 text-blue-600" />
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
          Methodological Boundaries & Limitations
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-600 leading-relaxed">
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
          <strong className="text-slate-900 block font-semibold text-xs">
            1. Phone GNSS Sampling Frequency
          </strong>
          <p className="text-[11px] text-slate-500">
            Raw smartphone GNSS coordinates in IO-VNBD Driver E refresh at ~0.1 Hz (~9–10s intervals).
            The IDR engine exclusively processes genuinely new fixes and ignores stale or duplicate updates.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
          <strong className="text-slate-900 block font-semibold text-xs">
            2. Thermal MEMS Gyro Drift
          </strong>
          <p className="text-[11px] text-slate-500">
            Consumer smartphone MEMS gyroscopes experience thermal drift that accumulates unconstrained over outages exceeding 40 seconds.
            Without road-network map matching or external odometry, the &lt;10% drift target is currently missed.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
          <strong className="text-slate-900 block font-semibold text-xs">
            3. Recorded Dataset Demonstration
          </strong>
          <p className="text-[11px] text-slate-500">
            This web interface streams recorded IO-VNBD sensor runs through a local desktop Python SDK.
            It is not live smartphone sensing and not certified for safety-critical aviation or automotive autopilot.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
          <strong className="text-slate-900 block font-semibold text-xs">
            4. No Arbitrary Baselines
          </strong>
          <p className="text-[11px] text-slate-500">
            Comparison baselines (frozen position, last speed) are only defined for standardized benchmark blackout windows,
            not manual interactive toggling. All evaluation numbers are presented without inflation.
          </p>
        </div>
      </div>
    </div>
  );
}
