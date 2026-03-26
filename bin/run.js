#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');

const serverPath = path.join(__dirname, '..', 'src', 'server.py');
const pdfDir = process.env.PDF_DIR || path.join(__dirname, '..', 'data', 'pdfs');

const proc = spawn('python', [serverPath], {
  env: { ...process.env, PDF_DIR: pdfDir },
  stdio: 'inherit'   // passa stdin/stdout direto — protocolo MCP stdio
});

proc.on('exit', (code) => process.exit(code));