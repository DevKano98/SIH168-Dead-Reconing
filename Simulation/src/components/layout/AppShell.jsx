import React from 'react';
import { TopNavigation } from './TopNavigation';
import { Sidebar } from './Sidebar';

export function AppShell({
  activePage,
  setActivePage,
  currentSection,
  setCurrentSection,
  connectionStatus,
  retryConnection,
  snapshot,
  children,
}) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      <TopNavigation
        activePage={activePage}
        setActivePage={setActivePage}
        connectionStatus={connectionStatus}
        retryConnection={retryConnection}
        snapshot={snapshot}
      />
      <div className="flex-1 flex w-full">
        {activePage === 'studio' && (
          <Sidebar
            currentSection={currentSection}
            setCurrentSection={setCurrentSection}
            connectionStatus={connectionStatus}
          />
        )}
        <div className="flex-1 w-full overflow-x-hidden">
          {children}
        </div>
      </div>
    </div>
  );
}
