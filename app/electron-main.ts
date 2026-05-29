/**
 * Electron main process entry.
 * Creates the application window, handles dev mode,
 * and prepares IPC for image analysis.
 */
import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** Repository root (parent of `app/`). Works on any machine after clone. */
const repoRoot = path.resolve(__dirname, '..', '..');

const devServerPort = process.env.VITE_DEV_SERVER_PORT || '5173';
const devServerUrl =
  process.env.VITE_DEV_SERVER_URL || `http://localhost:${devServerPort}`;

const isDev = process.env.NODE_ENV === 'development' || process.env.VITE_DEV_SERVER_HOST;

let mainWindow: BrowserWindow | null = null;

const createWindow = () => {
  const preloadPath = path.resolve(__dirname, 'preload.js');
  console.log('Electron preload path:', preloadPath);

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      enableRemoteModule: false,
      nodeIntegration: false,
    },
  });

  const startUrl = isDev
    ? devServerUrl
    : `file://${path.join(__dirname, '../renderer/index.html')}`;
  mainWindow.loadURL(startUrl);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
};

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Function to call the Python GEN pipeline query function
async function callPythonQuery(imagePath: string, mode: 'image' | 'crop', label?: string): Promise<any> {
  return new Promise((resolve, reject) => {
    // Create a temporary Python script to call the pipeline
    const tempScript = `
import sys
import os
import json
import traceback

project_root = os.environ.get("EESI_ROOT", ${JSON.stringify(repoRoot)})
sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

print("EESI project root:", project_root, file=sys.stderr)

try:
    from pipeline.query import query_from_image, query_from_crop
    from PIL import Image
    import os as _os

    print("Pipeline imported successfully", file=sys.stderr)

    # Load image
    image = Image.open('${imagePath}')
    print("Image loaded", file=sys.stderr)

    mode = ${JSON.stringify(mode)}
    label = ${label ? JSON.stringify(label) : 'None'}

    if mode == 'crop':
        if not label:
            raise ValueError('Crop mode requires a label')
        results = query_from_crop(image, label, k=5)
    else:
        results = query_from_image(image, k=5)

    print("Function called", mode, file=sys.stderr)

    if results is None:
        print(json.dumps({"success": False, "error": "No objects detected"}))
    else:
        formatted_results = []
        if mode == 'crop':
            formatted_matches = []
            for idx, match in enumerate(results, start=1):
                formatted_matches.append({
                    "id": f"m{idx}",
                    "name": f"{match['label']} - {_os.path.basename(match['image_path'])}",
                    "similarity": 1 - match['distance'],
                    "database": "GEN Database",
                    "details": f"Location: {match['city']}, {match['state']}, {match['country']} | Distance: {match['distance']:.3f}",
                    "imagePath": match['image_path'],
                    "imageData": match.get('image_data'),
                    "imageRetrievalError": match.get('image_retrieval_error')
                })
            formatted_results.append({
                "id": "1",
                "label": label,
                "confidence": 0.9,
                "boundingBox": {"x": 0, "y": 0, "width": 100, "height": 100},
                "matches": formatted_matches
            })
        else:
            for idx, (obj_label, matches) in enumerate(results.items(), start=1):
                formatted_matches = []
                for midx, match in enumerate(matches, start=1):
                    formatted_matches.append({
                        "id": f"m{midx}",
                        "name": f"{match['label']} - {_os.path.basename(match['image_path'])}",
                        "similarity": 1 - match['distance'],
                        "database": "GEN Database",
                        "details": f"Location: {match['city']}, {match['state']}, {match['country']} | Distance: {match['distance']:.3f}",
                        "imagePath": match['image_path'],
                        "imageData": match.get('image_data'),
                        "imageRetrievalError": match.get('image_retrieval_error')
                    })
                formatted_results.append({
                    "id": str(idx),
                    "label": obj_label,
                    "confidence": 0.9,
                    "boundingBox": {"x": 0, "y": 0, "width": 100, "height": 100},
                    "matches": formatted_matches
                })

        print(json.dumps({"success": True, "objects": formatted_results}))

except Exception as e:
    print("Exception:", str(e), file=sys.stderr)
    print("Traceback:", traceback.format_exc(), file=sys.stderr)
    print(json.dumps({"success": False, "error": str(e), "traceback": traceback.format_exc()}))
`;

    // Write temp script to file
    const tempScriptPath = path.join(__dirname, 'temp_query.py');
    fs.writeFileSync(tempScriptPath, tempScript);

    const pythonExecutable = process.env.PYTHON_EXECUTABLE || 'python3';

    // Run Python script
    const python = spawn(pythonExecutable, [tempScriptPath], {
      cwd: repoRoot,
      env: {
        ...process.env,
        EESI_ROOT: repoRoot,
        PYTHONPATH: repoRoot,
      },
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    let output = '';
    let errorOutput = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    python.on('close', (code) => {
      // Clean up temp file
      try {
        fs.unlinkSync(tempScriptPath);
        fs.unlinkSync(imagePath);  // Clean up temp image
      } catch (e) {
        // Ignore cleanup errors
      }

      if (code === 0) {
        try {
          const result = JSON.parse(output.trim());
          resolve(result);
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${output}`));
        }
      } else {
        reject(new Error(`Python script failed: ${errorOutput}`));
      }
    });

    python.on('error', (error) => {
      // Clean up temp file
      try {
        fs.unlinkSync(tempScriptPath);
        fs.unlinkSync(imagePath);
      } catch (e) {
        // Ignore cleanup errors
      }
      reject(error);
    });
  });
}

// IPC handlers for image analysis
ipcMain.handle('analyze-image', async (event, payload: { imageData: string; mode: 'image' | 'crop'; label?: string }) => {
  console.log('IPC handler called with mode:', payload.mode);
  console.log('IPC handler called with image data length:', payload.imageData.length);

  try {
    console.log('Converting base64 to image...');
    // Convert base64 to temporary image file
    const base64Data = payload.imageData.replace(/^data:image\/[a-z]+;base64,/, '');
    const imageBuffer = Buffer.from(base64Data, 'base64');

    // Create temporary image file
    const tempImagePath = path.join(__dirname, `temp_image_${Date.now()}.png`);
    fs.writeFileSync(tempImagePath, imageBuffer);
    console.log('Created temp image:', tempImagePath);

    // Call Python function
    console.log('Calling Python function...');
    const result = await callPythonQuery(tempImagePath, payload.mode, payload.label);
    console.log('Python result:', result);

    return result;
  } catch (error) {
    console.error('Analysis failed:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    };
  }
});
