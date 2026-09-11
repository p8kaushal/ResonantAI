import React, { useState, useEffect } from 'react';

const electron = (window as any).require ? (window as any).require('electron') : null;
const ipcRenderer = electron ? electron.ipcRenderer : null;

export const App: React.FC = () => {
  const [engineActive, setEngineActive] = useState(true);
  const [latencyMs, setLatencyMs] = useState(28);

  useEffect(() => {
    if (!ipcRenderer) return;
    const handleToggleEngine = (_: any, active: boolean) => {
      setEngineActive(active);
    };
    ipcRenderer.on('toggle-engine', handleToggleEngine);
    return () => {
      ipcRenderer.removeListener('toggle-engine', handleToggleEngine);
    };
  }, []);

  const handleToggle = () => {
    const nextState = !engineActive;
    setEngineActive(nextState);
    if (ipcRenderer) {
      ipcRenderer.send('engine-state-changed', nextState);
    }
  };

  return (
    <div className="w-full h-screen bg-slate-900 text-white p-4 flex flex-col justify-between font-sans select-none">
      <div>
        <div className="flex items-center justify-between border-b border-slate-700 pb-3">
          <h1 className="text-lg font-bold text-teal-400">Resonant AI</h1>
          <span className={`px-2 py-0.5 text-xs rounded-full ${engineActive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
            {engineActive ? 'Engine Active' : 'Bypassed'}
          </span>
        </div>

        <div className="mt-6 space-y-4">
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <label className="text-xs text-slate-400 block mb-1">Target Virtual Mic Output</label>
            <div className="text-sm font-semibold text-slate-200">BlackHole 2ch (Virtual Driver)</div>
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
              onChange={(e) => setLatencyMs(Number(e.target.value))}
              className="w-full accent-teal-400 cursor-pointer"
            />
          </div>
        </div>
      </div>

      <button
        onClick={handleToggle}
        className={`w-full py-2.5 rounded-lg font-bold text-sm transition-all ${
          engineActive ? 'bg-rose-600 hover:bg-rose-700 text-white' : 'bg-teal-500 hover:bg-teal-600 text-slate-950'
        }`}
      >
        {engineActive ? 'Disable Audio Processing' : 'Enable Resonant Engine'}
      </button>
    </div>
  );
};

export default App;
