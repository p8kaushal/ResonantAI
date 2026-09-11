const { app, BrowserWindow, Tray, Menu, ipcMain, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const { execSync, spawn } = require('child_process');

let tray = null;
let window = null;
let engineActive = true;
let pyDaemon = null;

function spawnAudioDaemon() {
  try {
    const projectRoot = path.join(__dirname, '..');
    const venvPath = path.join(projectRoot, 'venv/bin/python');
    const pyCmd = fs.existsSync(venvPath) ? venvPath : 'python3';
    const daemonPath = path.join(projectRoot, 'src/audio/audio_daemon.py');
    
    pyDaemon = spawn(pyCmd, [daemonPath], {
      cwd: projectRoot,
      env: { ...process.env, PYTHONPATH: projectRoot },
      stdio: ['pipe', 'pipe', 'pipe']
    });

    const readline = require('readline');
    const rl = readline.createInterface({ input: pyDaemon.stdout });

    rl.on('line', (line) => {
      if (!line.trim()) return;
      try {
        const msg = JSON.parse(line.trim());
        if (window && !window.isDestroyed()) {
          if (msg.type === 'level') {
            window.webContents.send('audio-level', msg.val);
          } else if (msg.type === 'latency_ack') {
            window.webContents.send('latency-updated', msg.ms);
          }
        }
      } catch (e) {}
    });

    pyDaemon.stderr.on('data', (data) => {
      console.error(`[Python Daemon Error] ${data.toString().trim()}`);
    });

    setTimeout(() => {
      if (pyDaemon && pyDaemon.stdin && !pyDaemon.killed) {
        try {
          pyDaemon.stdin.write(JSON.stringify({
            command: 'init_stream',
            input: 0,
            output: 1,
            ms: 28
          }) + '\n');
        } catch (e) {
          console.error('[Electron Main] Init daemon write error:', e.message);
        }
      }
    }, 300);
  } catch (err) {
    console.error('[Electron Main] Failed to spawn audio daemon:', err.message);
  }
}

function sendDaemonCommand(cmdObj) {
  if (pyDaemon && pyDaemon.stdin && !pyDaemon.killed) {
    try {
      pyDaemon.stdin.write(JSON.stringify(cmdObj) + '\n');
    } catch (e) {
      console.error('[Electron Main] Daemon write error:', e.message);
    }
  }
}

function createMenu() {
  return Menu.buildFromTemplate([
    {
      label: 'Show Control Center',
      click: () => {
        if (window) {
          if (window.isMinimized()) window.restore();
          window.show();
          window.focus();
        }
      }
    },
    {
      label: 'Toggle Resonant AI',
      type: 'checkbox',
      checked: engineActive,
      click: (item) => {
        engineActive = item.checked;
        sendDaemonCommand({ command: 'toggle_engine', active: engineActive });
        if (window) {
          window.webContents.send('toggle-engine', engineActive);
        }
        console.log(`[IPC Main] Audio Engine Processing: ${engineActive ? 'ENABLED' : 'DISABLED'}`);
      }
    },
    { type: 'separator' },
    { label: 'Quit', click: () => app.quit() }
  ]);
}

app.whenReady().then(() => {
  window = new BrowserWindow({
    width: 360,
    height: 520,
    show: false,
    frame: false,
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  const indexPath = path.join(__dirname, '../dist/index.html');
  window.loadFile(indexPath);

  window.once('ready-to-show', () => {
    window.show();
    window.focus();
  });

  window.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`[Renderer Log] ${message} (${path.basename(sourceId || '')}:${line})`);
  });

  const rawIconPath = path.join(__dirname, '../assets/tray_icon.png');
  const safeIcon = fs.existsSync(rawIconPath) ? rawIconPath : nativeImage.createEmpty();
  tray = new Tray(safeIcon);

  tray.setToolTip('Resonant AI - Active (<35ms)');
  tray.setContextMenu(createMenu());

  spawnAudioDaemon();

  ipcMain.handle('get-audio-devices', async () => {
    try {
      const venvPath = path.join(__dirname, '../venv/bin/python');
      const pyCmd = fs.existsSync(venvPath) ? `"${venvPath}"` : 'python3';
      const cmd = `${pyCmd} -c "import json, sys; sys.path.insert(0, '.'); from src.audio.stream_manager import AudioStreamManager; mgr = AudioStreamManager(); print(json.dumps(mgr.get_system_audio_devices()))"`;
      const output = execSync(cmd, { cwd: path.join(__dirname, '..'), encoding: 'utf8' });
      return JSON.parse(output.trim());
    } catch (err) {
      console.error('[IPC Main] Device fetch error:', err.message);
      return {
        inputs: [{ index: 0, name: 'MacBook Air Microphone', channels: 1 }],
        outputs: [
          { index: 1, name: 'MacBook Air Speakers', channels: 2 },
          { index: 2, name: 'BlackHole 2ch (Virtual Driver)', channels: 2 }
        ]
      };
    }
  });

  ipcMain.on('set-audio-devices', (event, { inputIndex, outputIndex }) => {
    console.log(`[IPC Main] Setting active input: ${inputIndex}, output: ${outputIndex}`);
    sendDaemonCommand({ command: 'set_devices', input: inputIndex, output: outputIndex });
  });

  ipcMain.on('set-latency', (event, ms) => {
    console.log(`[IPC Main] Latency buffer updated: ${ms} ms`);
    sendDaemonCommand({ command: 'set_latency', ms });
  });

  ipcMain.on('engine-state-changed', (event, active) => {
    engineActive = active;
    sendDaemonCommand({ command: 'toggle_engine', active: active });
    tray.setContextMenu(createMenu());
    if (window) {
      window.webContents.send('toggle-engine', active);
    }
    console.log(`[IPC Main] Audio Engine Processing: ${active ? 'ENABLED' : 'DISABLED'}`);
  });
});

app.on('will-quit', () => {
  if (pyDaemon) {
    pyDaemon.kill();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
