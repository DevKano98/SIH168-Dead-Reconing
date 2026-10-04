import React from 'react';
import { PlayCircle, Eye, BarChart2, Database, Settings, Cpu } from 'lucide-react';
import { APP_VERSION } from '../../utils/constants';

export function Sidebar({ currentSection, setCurrentSection, connectionStatus }) {
  const navItems = [
    { id: 'simulation', label: 'Simulation', icon: PlayCircle },
    { id: 'live-view', label: 'Live View', icon: Eye },
    { id: 'historical', label: 'Historical Analysis', icon: BarChart2 },
    { id: 'datasets', label: 'Datasets', icon: Database },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-[220px] flex-shrink-0 bg-white border-r border-slate-200 hidden lg:flex flex-col justify-between p-4 select-none min-h-[calc(100vh-64px)]">
      {/* Top Nav Rail */}
      <div className="space-y-6">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3">
          EXPERIMENT ENGINE
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isSelected = currentSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentSection(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  isSelected
                    ? 'bg-blue-50 text-blue-600 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Icon className={`w-4 h-4 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Technical Status & Metadata */}
      <div className="pt-4 border-t border-slate-100 space-y-3">
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
            <Cpu className="w-3.5 h-3.5 text-blue-600" />
            <span>Continuum SDK</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
            <span
              className={`w-2 h-2 rounded-full ${
                connectionStatus === 'connected' ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            />
            <span className="capitalize">{connectionStatus === 'connected' ? 'Engine Ready' : 'Engine Offline'}</span>
          </div>
          <div className="text-[10px] font-mono text-slate-400">v{APP_VERSION} (Python 3.10)</div>
        </div>
      </div>
    </aside>
  );
}
