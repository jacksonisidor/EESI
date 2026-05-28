/**
 * Shared TypeScript interface definitions for GEN Investigator.
 */
export interface DetectedObject {
  id: string;
  label: string;
  confidence: number;
  matches: Match[];
  boundingBox: { x: number; y: number; width: number; height: number };
}

export interface Match {
  id: string;
  name: string;
  similarity: number;
  database: string;
  details: string;
  imagePath?: string;
  imageData?: string;
  imageRetrievalError?: string;
}

export interface AnalysisRequest {
  imageData: string;
  mode: 'image' | 'crop';
  label?: string;
}

export interface AnalysisResult {
  success: boolean;
  objects: DetectedObject[];
  error?: string;
}

declare global {
  interface Window {
    electron: {
      analyzeImage: (payload: AnalysisRequest) => Promise<AnalysisResult>;
    };
  }
}
