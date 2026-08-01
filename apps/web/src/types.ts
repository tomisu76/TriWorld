export type MapSizeKey = 'S' | 'M' | 'L' | 'XL';

export interface MapSizeConfig {
  key: MapSizeKey;
  label: string;
  extentMeters: number;
}

export const MAP_SIZES: Record<MapSizeKey, MapSizeConfig> = {
  S: { key: 'S', label: 'S (512m)', extentMeters: 512 },
  M: { key: 'M', label: 'M (1024m)', extentMeters: 1024 },
  L: { key: 'L', label: 'L (2048m)', extentMeters: 2048 },
  XL: { key: 'XL', label: 'XL (4096m)', extentMeters: 4096 },
};

export type GenerationStage =
  | 'idle'
  | 'Preparing area'
  | 'Building synthetic canary'
  | 'Validating BeamNG package'
  | 'Ready'
  | 'error';

export interface LocationSelection {
  latitude: number;
  longitude: number;
}

export interface GenerationRequest {
  latitude: number;
  longitude: number;
  size: MapSizeKey;
  extentMeters: number;
}

export interface GenerationResponse {
  jobId: string;
  status: string;
}

export interface JobStatusResponse {
  jobId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  stage: string;
  progress: number;
  error: string | null;
  downloadUrl: string | null;
}
