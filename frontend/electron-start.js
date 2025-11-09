// Simple Electron launcher
// This file just launches Electron pointing to the main.js file

const electron = require('electron');
const { spawn } = require('child_process');
const path = require('path');

const electronPath = electron;
const mainPath = path.join(__dirname, 'electron', 'main.js');

console.log('Launching Electron...');
console.log('Electron path:', electronPath);
console.log('Main file:', mainPath);

const proc = spawn(electronPath, [mainPath], {
  stdio: 'inherit',
  env: {
    ...process.env,
    NODE_ENV: 'development'
  }
});

proc.on('close', (code) => {
  process.exit(code);
});
