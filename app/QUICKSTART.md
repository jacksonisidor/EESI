<!-- Quickstart guide for the GEN Investigator Electron app. -->
# 🚀 GEN Investigator Electron App - QUICKSTART

Your fully functional Electron app is ready! Here's how to run it:

## Quick Start (30 seconds)

```bash
cd app
npm run electron-dev
```

That's it! The app will:
✅ Start the Vite dev server (http://localhost:5173)
✅ Launch the Electron app with DevTools
✅ Load with hot-reload enabled for live code changes

## What's Built

### ✨ Main Features
- **Image Upload** - Drag or click to upload images
- **Object Detection** - Uses GEN Python pipeline via `query_from_image()` in `pipeline/query.py`
- **Match Results** - Database matches with similarity scores
- **Export** - Save analysis results as JSON

### 📦 Tech Stack
- **Electron 31** - Desktop app framework
- **React 18** - UI library  
- **TypeScript** - Type-safe code
- **Tailwind CSS** - Beautiful dark theme UI
- **Vite** - Lightning-fast dev server

### 🔒 Security
- Context isolation enabled
- Preload script for safe IPC
- No node integration in renderer

## Project Layout

```
app/
├── src/                          # React application
│   ├── App.tsx                   # Main UI component  
│   ├── main.tsx                  # React entry point
│   ├── index.css                 # Tailwind styles
│   └── types.ts                  # TypeScript definitions
├── electron-main.ts              # Electron main process
├── electron-preload.ts           # IPC security layer
├── package.json                  # Dependencies & scripts
├── vite.config.ts                # Vite configuration
└── README.md                      # Full documentation
```

## Available Commands

| Command | Purpose |
|---------|---------|
| `npm run electron-dev` | Run dev server + open Electron app |
| `npm run dev` | Vite dev server only |
| `npm run build` | Build for production |
| `npm run build:vite` | Build React app only |
| `npm run build:electron` | Build Electron process only |

## Next: Customize Detection Backend

The app currently uses the GEN Python pipeline via `query_from_image()` in `pipeline/query.py`. To connect a different backend or cloud API:

### Option 1: Cloud APIs (Easiest)
```typescript
// electron-main.ts - Update the IPC handler
ipcMain.handle('analyze-image', async (event, imageData) => {
  const results = await callCloudVisionAPI(imageData);
  return { success: true, objects: results };
});
```

Popular options:
- **AWS Rekognition** - https://aws.amazon.com/rekognition/
- **Google Cloud Vision** - https://cloud.google.com/vision
- **Azure Computer Vision** - https://azure.microsoft.com/services/cognitive-services/computer-vision/

### Option 2: Local ML Models
- Install TensorFlow.js or ONNX Runtime
- Run inference in Electron process
- Zero latency, works offline

### Option 3: Python Backend
- Run a Python service for heavy computation
- Call from Node.js via child_process
- Great for complex ML pipelines

## Development Tips

### 🔥 Hot Reloading
Edit any React component and see changes instantly - no refresh needed!

### 🐛 Debugging
- React DevTools: Inspect components, props, state
- Electron DevTools: Debug main process, network, storage
- Both open automatically in dev mode

### 📱 Testing
- Dev server on http://localhost:5173 for quick web testing
- Electron app for full desktop features
- Switch between them easily during development

### 🎨 Styling
All styling uses **Tailwind CSS** in `src/index.css`. Customize:
- Colors in `tailwind.config.ts`
- Global styles in `src/index.css`
- Component styles inline in `src/App.tsx`

## Building for Release

```bash
npm run build
```

This creates:
- Optimized bundles (Vite handles React)
- Packaged Electron app (DMG for Mac, EXE for Windows, etc.)
- Installers in `dist/` ready to distribute

## Troubleshooting

**"Port 5173 already in use"**
```bash
lsof -ti :5173 | xargs kill -9
```

**DevTools open by default and want it closed**
- Edit `electron-main.ts` line 23, remove: `if (isDev) { mainWindow.webContents.openDevTools(); }`

**Styles look broken**
- Restart dev server (Cmd+C, then `npm run electron-dev` again)
- Double-check `index.css` imports are correct

**Slow startup**
- First run downloads Electron (~150MB) - only happens once
- Subsequent runs start in ~2-3 seconds

## Project Structure Notes

- **`src/`** - All React code (builds to `dist/renderer/`)
- **`electron-*.ts`** - Main process code (builds to `dist/`)
- **`dist/`** - Production builds (gitignored)
- **`node_modules/`** - Dependencies (gitignored)
- **`dist/main.js`** - Electron entry point

## What's Next?

1. ✅ Run the app: `npm run electron-dev`
2. 📝 Try uploading an image - see the demo detection work
3. 🔌 Connect a real API for actual object detection
4. 💾 Consider adding database storage (Supabase, Firebase)
5. 📦 Build for production: `npm run build`

## Questions?

Refer to:
- Full docs: [README.md](README.md)
- TypeScript types: [src/types.ts](src/types.ts)
- Electron config: [electron-main.ts](electron-main.ts)
- UI code: [src/App.tsx](src/App.tsx)

---

**Happy coding!** 🎉

You now have a professional Electron desktop app ready for development.
