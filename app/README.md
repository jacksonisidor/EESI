<!-- GEN Investigator Electron app documentation and usage guide. -->
# GEN Investigator - Electron App

A professional desktop application for object detection and matching powered by Electron, React, TypeScript, and Tailwind CSS.

## Features

✨ **Image Upload & Analysis**
- Upload images for object detection
- Run the GEN Python pipeline through `query_from_image()` in `pipeline/query.py`
- Display confidence scores

🎯 **Object Matching**
- Shows detected objects in images (vehicles, people, buildings)
- Displays matching results from multiple databases
- Shows similarity scores and match details

💾 **Export Results**
- Export investigation results as JSON
- Timestamp each analysis for record-keeping

🎨 **Professional UI**
- Dark mode interface optimized for investigation work
- Responsive design for different screen sizes
- Real-time hot module reloading in development

## Project Structure

```
electron app/
├── src/
│   ├── main.tsx              # React entry point
│   ├── App.tsx               # Main application component
│   ├── index.css             # Global styles & Tailwind
│   ├── types.ts              # TypeScript type definitions
│   └── App.css               # Component styles
├── electron-main.ts          # Electron main process
├── electron-preload.ts       # IPC preload script
├── vite.config.ts            # Vite configuration
├── tailwind.config.ts        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
├── build-electron.mjs        # Build script for Electron
├── package.json              # Dependencies and scripts
└── index.html                # HTML entry point
```

## Development

### Prerequisites
- Node.js 18+ and npm
- macOS, Windows, or Linux

### Setup

```bash
cd "electron app"
npm install
```

### Run Development Server

```bash
npm run electron-dev
```

This launches:
- Vite dev server on http://localhost:5173
- Electron app with DevTools open
- Hot module reloading for code changes

### Available Commands

- `npm run dev` - Start Vite dev server only
- `npm run electron-dev` - Launch full Electron development with Vite
- `npm run build:electron` - Build Electron main process
- `npm run build:vite` - Build React app with Vite
- `npm run build` - Full production build
- `npm run make` - Package app with electron-builder

## Building for Production

```bash
npm run build
```

This will:
1. Compile Electron main process
2. Build optimized React app
3. Create distributable package using electron-builder

Generated installers will be in the `dist/` directory.

## How It Works

### Architecture

1. **Main Process** (`electron-main.ts`)
   - Manages app window and lifecycle
   - Handles IPC (Inter-Process Communication)
   - Calls the GEN Python pipeline via `query_from_image()` in `pipeline/query.py`

2. **Preload Script** (`electron-preload.ts`)
   - Safely exposes Electron APIs to renderer
   - Context isolation for security
   - Defines `window.electron.analyzeImage()`

3. **Renderer Process** (`src/App.tsx`)
   - React UI for image upload and results
   - Calls IPC handlers for analysis
   - Displays detection results

### Image Analysis Flow

1. User uploads an image
2. Image converted to base64 data URL
3. Sent to main process via IPC
4. GEN Python pipeline returns results via `query_from_image()` in `pipeline/query.py`
5. UI displays detected objects and matches

## Customization

### Customize the Detection Backend

This Electron app currently uses the GEN Python pipeline via `query_from_image()` in `pipeline/query.py`.

To connect a different backend or API:

1. Update the IPC handler in `electron-main.ts`:
```typescript
ipcMain.handle('analyze-image', async (event, imageData: string) => {
  // Call your real API here instead of returning mock data
  const results = await callYourDetectionAPI(imageData);
  return { success: true, objects: results };
});
```

2. Options:
   - Cloud Vision APIs: AWS Rekognition, Google Cloud Vision, Azure Computer Vision
   - Local models: TensorFlow.js, ONNX Runtime, PyTorch via node-gyp
   - Python backend: Call Python process from Node.js

### Styling

- Uses **Tailwind CSS v4** for styling
- Dark theme with slate colors
- Customize in `tailwind.config.ts`
- Global styles in `src/index.css`

### Database Integration

To store investigation results:

1. Add Supabase client to dependencies
2. Update IPC handlers to save results
3. Query historical investigations

## Integration with GEN Pipeline

This Electron app is now integrated with the GEN Python pipeline! When you click "Analyze Image", it:

1. **Converts** the uploaded image to a temporary file
2. **Calls** the `query_from_image()` function from `pipeline/query.py`
3. **Processes** the image through the full GEN pipeline (object detection, embedding, database matching)
4. **Returns** real matches from your database instead of mock data

### How It Works

- **IPC Communication**: Electron main process spawns Python subprocess
- **Image Processing**: Base64 images are saved as temp files for Python to read
- **Result Formatting**: Python results are converted to match the UI expectations
- **Error Handling**: Graceful fallbacks if Python processing fails

### Requirements

- Python 3.11+ with all dependencies from `requirements.txt`
- Database connection configured in the pipeline
- Models and embeddings set up

### Testing the Integration

The app will now show real object detection results instead of the previous mock data. Upload an image and click "Analyze" to see the GEN pipeline in action!

### Troubleshooting

**"No objects detected"**: The image might not contain detectable objects, or the model needs tuning
**Python errors**: Check that all dependencies are installed and the database is accessible
**Import errors**: Ensure the Python path is correctly set in the Electron main process

## Technologies

- **Electron 31** - Desktop app framework
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **Tailwind CSS v4** - Styling
- **Python 3.11+** - ML pipeline backend
- **PostgreSQL** - Vector database for matches
- **esbuild** - JS bundler

## Security

- ✅ Context isolation enabled
- ✅ Preload script for safe API exposure
- ✅ No nodeIntegration
- ✅ No enableRemoteModule

## Performance Tips

- Images are processed as base64, optimize large files
- Use debouncing for real-time analysis
- Consider worker threads for heavy computation
- Lazy load components as needed

## Troubleshooting

**Port 5173 already in use:**
```bash
# Kill the process using the port
lsof -ti :5173 | xargs kill -9
```

**Electron won't start:**
- Check Node version: `node --version` (require 18+)
- Clear `dist/` and `node_modules/`: `rm -rf dist node_modules && npm install`

**Styles not loading:**
- Restart dev server
- Check Tailwind config is correct
- Verify index.css imports are present

## License

Created for the GEN Investigator project.

## Support

For issues or questions, check the project documentation or the original Figma design file.
