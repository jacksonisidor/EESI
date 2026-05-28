/**
 * Main React application component.
 * Handles image upload, analysis flow, and result export.
 */
import { useState } from 'react';
import { Upload, Search, AlertCircle, Download } from 'lucide-react';

interface DetectedObject {
  id: string;
  label: string;
  confidence: number;
  matches: Match[];
  boundingBox: { x: number; y: number; width: number; height: number };
}

interface Match {
  id: string;
  name: string;
  similarity: number;
  database: string;
  details: string;
  imageData?: string;
  imageRetrievalError?: string;
  imagePath?: string;
}

function App() {
  const hasElectronBridge =
  typeof window !== 'undefined' &&
  typeof window.electron?.analyzeImage === 'function';
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [analysisMode, setAnalysisMode] = useState<'image' | 'crop'>('image');
  const [roomType, setRoomType] = useState<'bathroom' | 'other'>('bathroom');
  const [bathroomFeature, setBathroomFeature] = useState<
    | 'bathtub'
    | 'bidet'
    | 'brand'
    | 'floor'
    | 'mirror'
    | 'outlet'
    | 'plant'
    | 'rug'
    | 'shower'
    | 'showerhead'
    | 'sink'
    | 'toilet'
    | 'window'
  >('bathtub');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [detectedObjects, setDetectedObjects] = useState<DetectedObject[]>([]);
  const [selectedObject, setSelectedObject] = useState<string | null>(null);


  
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setUploadedImage(event.target?.result as string);
        setDetectedObjects([]);
        setSelectedObject(null);
      };
      reader.readAsDataURL(file);
    }
  };

 const analyzeImage = async () => {
  if (!uploadedImage) return;

  if (!hasElectronBridge) {
    alert('Electron bridge unavailable. Please run this app from the Electron shell, not the browser.');
    return;
  }

  setIsAnalyzing(true);
  try {
    const result = await window.electron.analyzeImage({
      imageData: uploadedImage,
      mode: analysisMode,
      label:
        analysisMode === 'crop'
          ? roomType === 'bathroom'
            ? bathroomFeature
            : 'other'
          : undefined,
    });

    if (result.success) {
      setDetectedObjects(result.objects);
      if (result.objects.length > 0) {
        setSelectedObject(result.objects[0].id);
      }
    } else {
      alert('Analysis failed: ' + (result.error || 'Unknown error'));
    }
  } catch (error) {
    alert('Analysis error: ' + error);
  } finally {
    setIsAnalyzing(false);
  }
};

  const exportResults = () => {
    if (detectedObjects.length === 0) return;

    const exportData = {
      timestamp: new Date().toISOString(),
      objects: detectedObjects,
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `investigation-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const selectedObjectData = detectedObjects.find((obj) => obj.id === selectedObject);

  return (
    <div className="bg-slate-950 text-slate-100 min-h-screen overflow-y-auto flex flex-col items-center">
      <div className="w-full max-w-5xl p-8 pt-16">
        {/* Header */}
        <div className="mb-12 border-b border-slate-800 pb-8 text-center">
          <h1 className="text-4xl font-bold text-slate-100 mb-2">GEN Investigator</h1>
          <p className="text-slate-400">Object Detection and Matching Interface</p>
        </div>

        {/* Main Grid */}
        <div style={{ marginTop: '48px' }} className="grid grid-cols-1 lg:grid-cols-[minmax(320px,380px)_minmax(0,1fr)] gap-8 w-full">
          {/* Upload Section */}
          <div className="lg:col-span-1">
            <div className="bg-slate-900 rounded-lg border border-slate-800 p-6 sticky top-8">
              <h2 className="text-lg font-semibold mb-4">Upload Image</h2>
                {!hasElectronBridge && (
  <div className="mb-4 rounded-lg border border-rose-700 bg-rose-950/30 p-4 text-sm text-rose-200">
    <p className="font-semibold">Electron bridge unavailable</p>
    <p>Please open this app using the Electron shell instead of the browser.</p>
  </div>
)}

              <div className="mb-4">
                <p className="text-sm text-slate-400 mb-2">Analysis mode</p>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setAnalysisMode('image')}
                    className={`rounded-lg py-2 text-sm font-medium transition ${
                      analysisMode === 'image'
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    Full Image
                  </button>
                  <button
                    type="button"
                    onClick={() => setAnalysisMode('crop')}
                    className={`rounded-lg py-2 text-sm font-medium transition ${
                      analysisMode === 'crop'
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    Crop + Label
                  </button>
                </div>
                <p className="mt-3 text-sm text-slate-500">
                  Use <strong>Full Image</strong> to detect objects automatically from the uploaded photo.
                  Use <strong>Crop + Label</strong> to search with a manually labeled region when you want a focused match.
                </p>
                {analysisMode === 'crop' && (
                  <div className="mt-3 space-y-4">
                    <div>
                      <label className="block text-sm text-slate-400 mb-2" htmlFor="roomType">
                        Room type
                      </label>
                      <select
                        id="roomType"
                        value={roomType}
                        onChange={(event) => setRoomType(event.target.value as 'bathroom' | 'other')}
                        className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-blue-500 focus:outline-none"
                      >
                        <option value="bathroom">bathroom</option>
                        <option value="other">other</option>
                      </select>
                    </div>

                    {roomType === 'bathroom' && (
                      <div>
                        <label className="block text-sm text-slate-400 mb-2" htmlFor="bathroomFeature">
                          Bathroom item
                        </label>
                        <select
                          id="bathroomFeature"
                          value={bathroomFeature}
                          onChange={(event) =>
                            setBathroomFeature(
                              event.target.value as
                                | 'bathtub'
                                | 'bidet'
                                | 'brand'
                                | 'floor'
                                | 'mirror'
                                | 'outlet'
                                | 'plant'
                                | 'rug'
                                | 'shower'
                                | 'showerhead'
                                | 'sink'
                                | 'toilet'
                                | 'window'
                            )
                          }
                          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 focus:border-blue-500 focus:outline-none"
                        >
                          <option value="bathtub">bathtub</option>
                          <option value="bidet">bidet</option>
                          <option value="brand">brand</option>
                          <option value="floor">floor</option>
                          <option value="mirror">mirror</option>
                          <option value="outlet">outlet</option>
                          <option value="plant">plant</option>
                          <option value="rug">rug</option>
                          <option value="shower">shower</option>
                          <option value="showerhead">showerhead</option>
                          <option value="sink">sink</option>
                          <option value="toilet">toilet</option>
                          <option value="window">window</option>
                        </select>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {!uploadedImage ? (
                <label className="flex flex-col items-center justify-center border-2 border-dashed border-slate-700 rounded-lg p-12 cursor-pointer hover:border-slate-600 transition-colors">
                  <Upload className="w-12 h-12 text-slate-500 mb-4" />
                  <span className="text-slate-400 mb-2 text-center font-medium">
                    Click to upload
                  </span>
                  <span className="text-sm text-slate-500 text-center">PNG, JPG, WEBP</span>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    className="hidden"
                  />
                </label>
              ) : (
                <div className="space-y-4">
                  <div className="relative rounded-lg border border-slate-700 overflow-y-auto max-h-[60vh]">
                        <img
                          src={uploadedImage}
                          alt="Uploaded"
                          className="w-full h-auto object-contain"
                        />
                      </div>

                  <div className="flex gap-2 flex-col">
                    <button
                      onClick={analyzeImage}
                      disabled={isAnalyzing || !hasElectronBridge}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors font-medium"
                    >
                      {isAnalyzing ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Search className="w-4 h-4" />
                          Analyze Image
                        </>
                      )}
                    </button>

                    <label className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 py-2 px-4 rounded-lg cursor-pointer text-center transition-colors font-medium">
                      Change Image
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageUpload}
                        className="hidden"
                      />
                    </label>

                    {detectedObjects.length > 0 && (
                      <button
                        onClick={exportResults}
                        className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors font-medium"
                      >
                        <Download className="w-4 h-4" />
                        Export Results
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Info Box */}
              <div className="mt-6 bg-blue-950/30 border border-blue-900/50 rounded-lg p-4 flex gap-3">
                <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-200">
                  <p className="font-semibold mb-1">Desktop App</p>
                  <p>
                    This Electron app calls `query_from_image()` or `query_from_crop()` in `pipeline/query.py` depending on the selected mode.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-1">
            {detectedObjects.length === 0 ? (
              <div className="bg-slate-900 rounded-lg border border-slate-800 p-12 flex flex-col items-center justify-center text-slate-500 h-96">
                <Search className="w-16 h-16 mb-4 opacity-30" />
                <p className="text-lg font-medium">No analysis results</p>
                <p className="text-sm mt-2">Upload and analyze an image to see matches</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {/* Object List */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {detectedObjects.map((obj) => (
                    <button
                      key={obj.id}
                      onClick={() => setSelectedObject(obj.id)}
                      className={`text-left p-4 rounded-lg border transition-all ${
                        selectedObject === obj.id
                          ? 'bg-blue-900/30 border-blue-600'
                          : 'bg-slate-800 border-slate-700 hover:border-slate-600'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-slate-100">{obj.label}</h3>
                        <span className="text-xs bg-green-900/30 text-green-400 px-2 py-1 rounded">
                          {(obj.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mt-2">
                        {obj.matches.length} match{obj.matches.length !== 1 ? 'es' : ''} found
                      </p>
                    </button>
                  ))}
                </div>

                {/* Detailed Results */}
                {selectedObjectData && (
                  <div className="bg-slate-900 rounded-lg border border-slate-800 p-6">
                    <h3 className="text-xl font-bold mb-6 text-slate-100">
                      {selectedObjectData.label} - Matches
                    </h3>

<div className="space-y-4 pr-2 max-h-[500px] overflow-y-auto">
  {selectedObjectData.matches.length === 0 ? (
    <p className="text-slate-400 text-center py-8">No matches found</p>
  ) : (
    selectedObjectData.matches.map((match, index) => (
      <div
        key={match.id}
        className="bg-slate-800 rounded-lg p-4 border border-slate-700 hover:border-slate-600 transition-colors"
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <p className="text-xs uppercase tracking-wide text-slate-500 mb-1">
              Match {index + 1}
            </p>
            <p className="font-semibold text-slate-100 mb-1">{match.name}</p>
            <p className="text-xs text-slate-500">{match.database}</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-slate-200">
              {(match.similarity * 100).toFixed(0)}%
            </p>
            <p className="text-xs text-slate-500">similarity</p>
          </div>
        </div>

        {match.imageData ? (
          <div className="mb-3 rounded-lg overflow-hidden border border-slate-700">
            <img
              src={`data:image/jpeg;base64,${match.imageData}`}
              alt={match.name}
              className="w-full h-auto object-cover"
            />
          </div>
        ) : match.imageRetrievalError ? (
          <div className="mb-3 rounded-lg border border-rose-500 bg-rose-950/10 p-3">
            <p className="text-sm text-rose-200 font-semibold">Image retrieval failed</p>
            <p className="text-xs text-rose-300 break-words">
              {match.imageRetrievalError}
            </p>
          </div>
        ) : null}

        <div className="w-full bg-slate-700 rounded-full h-2 mb-3">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${match.similarity * 100}%` }}
          />
        </div>

        <p className="text-sm text-slate-300 mb-2">{match.details}</p>

        {match.imagePath && (
          <p className="text-xs text-slate-500">Source: {match.imagePath}</p>
        )}
      </div>
    ))
  )}
</div>
                      
                    </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;