#!/bin/bash

# Start the GEN Investigator development environment with Vite and Electron.
# GEN Investigator - Quick Start Guide
# Navigate to the electron app directory and run the development server

cd "/Users/tsprouse/Documents/GitHub/GEN/electron app"

echo "🚀 Starting GEN Investigator Electron App..."
echo "   Building Electron main process..."
npm run build:electron

echo ""
echo "✅ Starting development server..."
echo "   • Vite dev server: http://localhost:5173"
echo "   • Electron app will open automatically"
echo "   • Changes to files will hot-reload"
echo ""
echo "🎨 App Features:"
echo "   • Upload images for object detection"
echo "   • View detected objects and matches"
echo "   • Export results as JSON"
echo ""

npm run electron-dev
