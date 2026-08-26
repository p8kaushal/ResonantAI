import React, { useState, useEffect } from 'react';

// Declaration for Electron IPC if available in window
declare global {
  interface Window {
    require?: (module: string) => any;
  }
}

export const App: React.FC = () => {
  const [engineActive, setEngineActive] = useState<boolean>(true);
  const [latencyMs, setLatencyMs] = useState<number>(28);

  useEffect(() => {
    // Listen for toggle-engine IPC events from Electron tray menu
    if (typeof window !== 'undefined' && window.require) {
      try {
        const { ipcRenderer } = window.require('electron');
        const handleToggle = (_event: any, active: boolean) => {
          setEngineActive(active);
        };
        ipcRenderer.on('toggle-engine', handleToggle);
        return () => {
          ipcRenderer.removeListener('toggle-engine', handleToggle);
        };
      } catch (err) {
        console.warn('Electron IPC not accessible:', err);
      }
    }
  }, []);

  const handleToggleEngine = () => {
    const nextState = !engineActive;
    setEngineActive(nextState);
    if (typeof window !== 'undefined' && window.require) {
      try {
        const { ipcRenderer } = window.require('electron');
        ipcRenderer.send('toggle-engine', nextState);
      } catch (err) {
        console.warn('Failed to send toggle-engine IPC:', err);
      }
    }
  };

  const handleLatencyChange = (newVal: number) => {
    setLatencyMs(newVal);
    if (typeof window !== 'undefined' && window.require) {
      try {
        const { ipcRenderer } = window.require('electron');
        ipcRenderer.send('set-latency', newVal);
      } catch (err) {
        console.warn('Failed to send set-latency IPC:', err);
      }
    }
  };

  return (
    <div className="w-full h-screen bg-slate-900 text-white p-4 flex flex-col justify-between font-sans select-none">
      <div>
        <div className="flex items-center justify-between border-b border-slate-700 pb-3">
          <h1 className="text-lg font-bold text-teal-400">Resonant AI</h1>
          <span
            className={`px-2 py-0.5 text-xs rounded-full font-medium transition-colors ${
              engineActive
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-rose-500/20 text-rose-400'
            }`}
          >
            {engineActive ? 'Engine Active' : 'Bypassed'}
          </span>
        </div>

        <div className="mt-6 space-y-4">
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <label className="text-xs text-slate-400 block mb-1">
              Target Virtual Mic Output
            </label>
            <div className="text-sm font-semibold text-slate-200">
              BlackHole 2ch (Virtual Driver)
            </div>
          </div>

          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>System Latency Budget</span>
              <span className="text-teal-400 font-bold">{latencyMs} ms</span>
            </div>
            <input
              type="range"
              min="15"
              max="50"
              value={latencyMs}
              onChange={(e) => handleLatencyChange(Number(e.target.value))}
              className="w-full accent-teal-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>15ms (Ultra Fast)</span>
              <span>50ms (High Fidelity)</span>
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={handleToggleEngine}
        className={`w-full py-2.5 rounded-lg font-bold text-sm transition-all shadow-md ${
          engineActive
            ? 'bg-rose-600 hover:bg-rose-700 text-white'
            : 'bg-teal-500 hover:bg-teal-600 text-slate-950'
        }`}
      >
        {engineActive ? 'Disable Audio Processing' : 'Enable Resonant Engine'}
      </button>
    </div>
  );
};

export default App;
