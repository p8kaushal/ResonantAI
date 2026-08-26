// electron/main.js
const { app, BrowserWindow, Tray, Menu, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

let tray = null;
let window = null;

function createWindow() {
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
        </body>
      </html>
    `;
    window.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(fallbackHtml)}`);
  }

  // Hide window when it loses focus
  window.on('blur', () => {
    if (!window.webContents.isDevToolsOpened()) {
      window.hide();
    }
  });
}

function createTray() {
  const iconPath = path.join(__dirname, '../assets/tray_icon.png');
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Control Center',
      click: () => {
        if (window) {
          window.show();
          window.focus();
        }
      }
    },
    {
      label: 'Toggle Resonant AI',
      type: 'checkbox',
      checked: true,
      click: (item) => {
        if (window && window.webContents) {
          window.webContents.send('toggle-engine', item.checked);
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip('Resonant AI - Active (<35ms)');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (window.isVisible()) {
      window.hide();
    } else {
      window.show();
      window.focus();
    }
  });
}

app.whenReady().then(() => {
  createWindow();
  createTray();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// IPC communication handlers
ipcMain.on('get-engine-status', (event) => {
  event.reply('engine-status', { active: true, latencyMs: 28 });
});

ipcMain.on('toggle-engine', (event, active) => {
  console.log(`[Resonant AI] Engine toggled: ${active ? 'Active' : 'Disabled'}`);
});

ipcMain.on('set-latency', (event, latencyMs) => {
  console.log(`[Resonant AI] Latency updated: ${latencyMs} ms`);
});

ipcMain.on('close-window', () => {
  if (window) window.hide();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
