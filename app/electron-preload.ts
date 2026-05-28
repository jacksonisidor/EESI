/**
 * Electron preload script.
 * Exposes a secure IPC bridge to the renderer process.
 */
import { contextBridge, ipcRenderer } from 'electron';

console.log('Electron preload script loaded');

contextBridge.exposeInMainWorld('electron', {
  analyzeImage: (payload: { imageData: string; mode: 'image' | 'crop'; label?: string }) =>
    ipcRenderer.invoke('analyze-image', payload),
});
