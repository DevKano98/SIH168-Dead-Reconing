import React from 'react';
import { Compass, Satellite, Activity } from 'lucide-react';

export function SimulationHeader() {
  return (
    <div className="relative overflow-hidden bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
      {/* Subtle abstract technical grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(#2563EB 1px, transparent 1px)',
          backgroundSize: '16px 16px',
        }}
      />

      <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-50 border border-blue-100 text-[10px] font-bold uppercase tracking-wider text-blue-700">
            <Activity className="w-3 h-3 text-blue-600" />
            <span>GPS / GNSS SIMULATION ENVIRONMENT</span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 mt-1.5">
            Test. Observe. Improve.
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
            Simulate GPS scenarios, evaluate positioning performance, and analyze dead-reckoning drift with real-world sensor accuracy.
          </p>
        </div>

        <div className="hidden md:flex items-center gap-2 self-start sm:self-auto text-xs text-slate-500 font-mono">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200">
            <Satellite className="w-3.5 h-3.5 text-blue-600" />
            <span>IO-VNBD Dataset</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200">
            <Compass className="w-3.5 h-3.5 text-blue-600" />
            <span>10 Hz IMU Stream</span>
          </div>
        </div>
      </div>
    </div>
  );
}
