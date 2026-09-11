import React, { useState, useEffect } from 'react';

let ipcRenderer: any = null;
try {
  if (typeof window !== 'undefined' && (window as any).require) {
    ipcRenderer = (window as any).require('electron').ipcRenderer;
  }
} catch (e) {
  console.warn('IPC Renderer unavailable');
}

export const App: React.FC = () => {
  const [engineActive, setEngineActive] = useState(true);
  const [latencyMs, setLatencyMs] = useState(28);
  const [isRebuffering, setIsRebuffering] = useState(false);
  const [inputDevices, setInputDevices] = useState<any[]>([
    { index: 0, name: 'MacBook Air Microphone' }
  ]);
  const [outputDevices, setOutputDevices] = useState<any[]>([
    { index: 1, name: 'MacBook Air Speakers' },
    { index: 2, name: 'BlackHole 2ch (Virtual Driver)' }
  ]);
  const [selectedInput, setSelectedInput] = useState(0);
  const [selectedOutput, setSelectedOutput] = useState(1);
  const [audioLevel, setAudioLevel] = useState(0);

  useEffect(() => {
    if (!ipcRenderer) return;

    ipcRenderer.invoke('get-audio-devices')
      .then((res: any) => {
        if (res?.inputs?.length) setInputDevices(res.inputs);
        if (res?.outputs?.length) setOutputDevices(res.outputs);
      })
      .catch((err: any) => console.error('Device load error:', err));

    const handleToggle = (_: any, active: boolean) => setEngineActive(active);
    ipcRenderer.on('toggle-engine', handleToggle);

    const handleAudioLevel = (_: any, level: number) => {
      setAudioLevel(level);
    };
    ipcRenderer.on('audio-level', handleAudioLevel);

    const handleLatencyUpdated = (_: any, updatedMs: number) => {
      setIsRebuffering(false);
    };
    ipcRenderer.on('latency-updated', handleLatencyUpdated);

    return () => {
      ipcRenderer.removeListener('toggle-engine', handleToggle);
      ipcRenderer.removeListener('audio-level', handleAudioLevel);
      ipcRenderer.removeListener('latency-updated', handleLatencyUpdated);
    };
  }, []);

  const handleToggle = () => {
    const nextState = !engineActive;
    setEngineActive(nextState);
    if (ipcRenderer) {
      ipcRenderer.send('engine-state-changed', nextState);
    }
  };

  const handleDeviceChange = (inputId: number, outputId: number) => {
    setSelectedInput(inputId);
    setSelectedOutput(outputId);
    if (ipcRenderer) {
      ipcRenderer.send('set-audio-devices', { inputIndex: inputId, outputIndex: outputId });
    }
  };

  return (
    <div className="w-full h-screen bg-slate-900 text-white p-4 flex flex-col justify-between font-sans select-none overflow-y-auto">
      <div>
        <div className="flex items-center justify-between border-b border-slate-700 pb-3">
          <h1 className="text-lg font-bold text-teal-400">Resonant AI</h1>
          <span className={`px-2 py-0.5 text-xs rounded-full ${engineActive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
            {engineActive ? 'Engine Active' : 'Bypassed'}
          </span>
        </div>

        <div className="mt-4 space-y-3">
          {/* Input Microphone */}
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <label className="text-xs text-slate-400 block mb-1 font-medium">Input Microphone</label>
            <select
              value={selectedInput}
              onChange={(e) => handleDeviceChange(Number(e.target.value), selectedOutput)}
              className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded p-1.5 focus:outline-none focus:border-teal-400 cursor-pointer"
            >
              {inputDevices.map((dev) => (
                <option key={dev.index} value={dev.index}>
                  {dev.name}
                </option>
              ))}
            </select>
          </div>

          {/* Output Destination */}
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <label className="text-xs text-slate-400 block mb-1 font-medium">Output Destination</label>
            <select
              value={selectedOutput}
              onChange={(e) => handleDeviceChange(selectedInput, Number(e.target.value))}
              className="w-full bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded p-1.5 focus:outline-none focus:border-teal-400 cursor-pointer"
            >
              {outputDevices.map((dev) => (
                <option key={dev.index} value={dev.index}>
                  {dev.name}
                </option>
              ))}
            </select>
          </div>

          {/* Live Mic Signal (Continuous input level monitoring) */}
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <div className="flex justify-between text-xs text-slate-400 mb-1 font-medium">
              <span>Live Mic Signal</span>
              <span className="text-teal-400 font-bold">{audioLevel}%</span>
            </div>
            <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-700">
              <div
                className={`h-full transition-all duration-150 ${engineActive ? 'bg-gradient-to-r from-teal-500 to-emerald-400' : 'bg-amber-500'}`}
                style={{ width: `${audioLevel}%` }}
              />
            </div>
          </div>

          {/* System Latency Budget */}
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700">
            <div className="flex justify-between text-xs text-slate-400 mb-1 font-medium">
              <span>System Latency Budget</span>
              <span className="text-teal-400 font-bold">
                {isRebuffering ? `Applying ${latencyMs} ms buffer...` : `${latencyMs} ms`}
              </span>
            </div>
            <input
              type="range"
              min="15"
              max="50"
              value={latencyMs}
              onChange={(e) => {
                const val = Number(e.target.value);
                setLatencyMs(val);
                setIsRebuffering(true);
                if (ipcRenderer) {
                  ipcRenderer.send('set-latency', val);
                }
              }}
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
