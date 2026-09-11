const { app, BrowserWindow, Tray, Menu, ipcMain, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');

let tray = null;
let window = null;
let engineActive = true;

function createMenu() {
  return Menu.buildFromTemplate([
    { label: 'Show Control Center', click: () => window.show() },
    {
      label: 'Toggle Resonant AI',
      type: 'checkbox',
      checked: engineActive,
      click: (item) => {
        engineActive = item.checked;
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
    height: 480,
    show: false,
    frame: false,
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  const indexPath = path.join(__dirname, '../dist/index.html');
  if (fs.existsSync(indexPath)) {
    window.loadFile(indexPath);
  } else {
    // Fallback HTML if dist/index.html does not exist yet
    const fallbackHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8" />
          <title>Resonant AI Control Center</title>
          <style>
            body {
              background-color: #0f172a;
              color: #f8fafc;
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
              padding: 24px 16px;
              margin: 0;
              box-sizing: border-box;
              display: flex;
              flex-direction: column;
              height: 100vh;
              justify-content: space-between;
              user-select: none;
            }
            .header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              border-bottom: 1px solid #334155;
              padding-bottom: 12px;
            }
            .title {
              color: #2dd4bf;
              font-size: 18px;
              font-weight: 700;
              margin: 0;
            }
            .badge {
              background: rgba(16, 185, 129, 0.2);
              color: #34d399;
              padding: 2px 8px;
              border-radius: 9999px;
              font-size: 12px;
              font-weight: 500;
            }
            .card {
              background: #1e293b;
              border: 1px solid #334155;
              border-radius: 8px;
              padding: 12px;
              margin-top: 16px;
              text-align: left;
            }
            .card-label {
              font-size: 11px;
              color: #94a3b8;
              margin-bottom: 4px;
            }
            .card-value {
              font-size: 14px;
              font-weight: 600;
              color: #e2e8f0;
            }
            .btn {
              width: 100%;
              padding: 10px;
              border-radius: 8px;
              font-weight: 700;
              font-size: 14px;
              border: none;
              cursor: pointer;
              background-color: #e11d48;
              color: white;
            }
          </style>
        </head>
        <body>
          <div>
            <div class="header">
              <h1 class="title">Resonant AI</h1>
              <span class="badge" id="status-badge">Engine Active</span>
            </div>
            <div class="card">
              <div class="card-label">Target Virtual Mic Output</div>
              <div class="card-value">BlackHole 2ch (Virtual Driver)</div>
            </div>
            <div class="card">
              <div class="card-label">System Latency Budget</div>
              <div class="card-value" style="color: #2dd4bf;">28 ms (<35ms SLA)</div>
            </div>
          </div>
          <button class="btn" id="toggle-btn">Disable Audio Processing</button>
          <script>
            const { ipcRenderer } = require('electron');
            let active = true;
            const btn = document.getElementById('toggle-btn');
            const badge = document.getElementById('status-badge');

            function updateUI(isActive) {
              active = isActive;
              if (active) {
                badge.textContent = 'Engine Active';
                badge.style.background = 'rgba(16, 185, 129, 0.2)';
                badge.style.color = '#34d399';
                btn.textContent = 'Disable Audio Processing';
                btn.style.backgroundColor = '#e11d48';
                btn.style.color = '#ffffff';
              } else {
                badge.textContent = 'Bypassed';
                badge.style.background = 'rgba(244, 63, 94, 0.2)';
                badge.style.color = '#fb7185';
                btn.textContent = 'Enable Resonant Engine';
                btn.style.backgroundColor = '#14b8a6';
                btn.style.color = '#0f172a';
              }
            }

            btn.addEventListener('click', () => {
              const nextState = !active;
              updateUI(nextState);
              ipcRenderer.send('engine-state-changed', nextState);
            });

            ipcRenderer.on('toggle-engine', (event, state) => {
              updateUI(state);
            });
          </script>
        </body>
      </html>
    `;
    window.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(fallbackHtml)}`);
  }

  const rawIconPath = path.join(__dirname, '../assets/tray_icon.png');
  const safeIcon = fs.existsSync(rawIconPath) ? rawIconPath : nativeImage.createEmpty();
  tray = new Tray(safeIcon);

  tray.setToolTip('Resonant AI - Active (<35ms)');
  tray.setContextMenu(createMenu());

  tray.on('click', () => {
    if (window.isVisible()) {
      window.hide();
    } else {
      window.show();
      window.focus();
    }
  });

  ipcMain.on('engine-state-changed', (event, active) => {
    engineActive = active;
    tray.setContextMenu(createMenu());
    if (window) {
      window.webContents.send('toggle-engine', active);
    }
    console.log(`[IPC Main] Audio Engine Processing: ${active ? 'ENABLED' : 'DISABLED'}`);
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
