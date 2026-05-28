#!/usr/bin/env node

/**
 * Build script for the Electron main and preload processes.
 * Bundles TypeScript source files into ESM JavaScript output for Electron.
 */

import esbuild from 'esbuild';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Build main process
esbuild.buildSync({
  entryPoints: [path.join(__dirname, 'electron-main.ts')],
  bundle: true,
  platform: 'node',
  target: 'esnext',
  format: 'esm',
  outfile: path.join(__dirname, 'dist', 'main.js'),
  external: ['electron'],
});

// Build preload script
esbuild.buildSync({
  entryPoints: [path.join(__dirname, 'electron-preload.ts')],
  bundle: true,
  platform: 'node',
  target: 'esnext',
  format: 'cjs',
  outfile: path.join(__dirname, 'dist', 'preload.js'),
  external: ['electron'],
});

console.log('✓ Electron main process built');
