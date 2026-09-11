const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const distDir = path.join(__dirname, '../dist');
if (!fs.existsSync(distDir)) {
  fs.mkdirSync(distDir, { recursive: true });
}

// 1. Execute esbuild compilation via child_process
try {
  const entryFile = fs.existsSync(path.join(__dirname, '../src/ui/index.tsx'))
    ? path.join(__dirname, '../src/ui/index.tsx')
    : path.join(__dirname, '../src/ui/App.tsx');

  const bundlePath = path.join(distDir, 'bundle.js');
  
  // Exec esbuild via npx to avoid requiring node module directly
  execSync(`npx -y esbuild "${entryFile}" --bundle --outfile="${bundlePath}" --platform=browser --target=chrome100,node16 --loader:.tsx=tsx --loader:.ts=ts --loader:.js=jsx --define:process.env.NODE_ENV=\\"development\\"`, {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit'
  });

  console.log('[Build] esbuild successfully compiled React frontend to dist/bundle.js');
} catch (err) {
  console.warn('[Build Warning] esbuild CLI compilation note:', err.message);
}

// 2. Generate dist/index.html
const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Resonant AI Control Center</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-white overflow-hidden select-none">
  <div id="root"></div>
  <script src="bundle.js"></script>
</body>
</html>`;

fs.writeFileSync(path.join(distDir, 'index.html'), htmlContent);
console.log('[Build] Successfully generated dist/index.html');
