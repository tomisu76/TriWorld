import React from 'react';
import {
  MapSizeKey,
  MAP_SIZES,
  LocationSelection,
  GenerationStage,
} from '../types';

interface ControlPanelProps {
  selectedLocation: LocationSelection | null;
  mapSize: MapSizeKey;
  generationStage: GenerationStage;
  errorMessage: string | null;
  downloadUrl: string | null;
  isIonTokenMissing: boolean;
  onSelectMapSize: (size: MapSizeKey) => void;
  onGenerate: () => void;
  onDownload: () => void;
}

const STAGES: GenerationStage[] = [
  'Preparing area',
  'Building synthetic canary',
  'Validating BeamNG package',
  'Ready',
];

export const ControlPanel: React.FC<ControlPanelProps> = ({
  selectedLocation,
  mapSize,
  generationStage,
  errorMessage,
  downloadUrl,
  isIonTokenMissing,
  onSelectMapSize,
  onGenerate,
  onDownload,
}) => {
  const isGenerating =
    generationStage !== 'idle' &&
    generationStage !== 'Ready' &&
    generationStage !== 'error';

  const currentStageIndex = STAGES.indexOf(generationStage);

  return (
    <div className="control-panel">
      {/* Brand Header */}
      <div className="panel-header">
        <div className="brand-logo">
          <svg viewBox="0 0 24 24">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
        <div className="brand-title">TriWorld</div>
        <div className="brand-badge">v0.1</div>
      </div>

      {/* Cesium Ion Token Notice */}
      {isIonTokenMissing && (
        <div className="token-notice">
          ℹ️ <strong>Notice:</strong> Cesium Ion token is not configured.
          Using OpenStreetMap imagery and ellipsoid terrain.
        </div>
      )}

      {/* Synthetic Canary Bridge Truthful Notice */}
      <div className="token-notice" style={{ color: '#60a5fa', background: 'rgba(59, 130, 246, 0.1)', borderColor: 'rgba(59, 130, 246, 0.2)' }}>
        ℹ️ Current bridge build generates the verified synthetic canary. Geographic OSM/DEM compilation will be enabled in the next pipeline stage.
      </div>

      {/* Location Coordinates */}
      <div>
        <div className="section-label">Target Location</div>
        <div className="coords-box">
          {selectedLocation ? (
            <span className="coords-value">
              {selectedLocation.latitude}°N, {selectedLocation.longitude}°E
            </span>
          ) : (
            <span className="coords-placeholder">Click map to select location</span>
          )}
        </div>
      </div>

      {/* Map Size Selector */}
      <div>
        <div className="section-label">Map Size Extent</div>
        <div className="size-selector">
          {(Object.keys(MAP_SIZES) as MapSizeKey[]).map((key) => {
            const cfg = MAP_SIZES[key];
            return (
              <button
                key={key}
                className={`size-btn ${mapSize === key ? 'active' : ''}`}
                onClick={() => onSelectMapSize(key)}
                disabled={isGenerating}
              >
                {cfg.key}
              </button>
            );
          })}
        </div>
      </div>

      {/* Action Button */}
      <div>
        <button
          className="action-btn"
          disabled={!selectedLocation || isGenerating}
          onClick={onGenerate}
        >
          {isGenerating ? (
            <>
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                style={{ animation: 'spin 1s linear infinite' }}
              >
                <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
                <path d="M12 2a10 10 0 0 1 10 10" />
              </svg>
              Generating...
            </>
          ) : (
            'Generate BeamNG Map'
          )}
        </button>
      </div>

      {/* Generation Status Area */}
      {generationStage !== 'idle' && (
        <div className="status-area">
          <div className="section-label">Pipeline Status</div>
          {STAGES.map((stageName, idx) => {
            let stateClass = '';
            if (stageName === generationStage) {
              stateClass = 'active';
            } else if (currentStageIndex > idx) {
              stateClass = 'completed';
            }

            return (
              <div key={stageName} className={`stage-item ${stateClass}`}>
                <div className="stage-icon">
                  {stateClass === 'completed' && '✓'}
                </div>
                <span>{stageName}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Error Display */}
      {errorMessage && <div className="error-banner">❌ {errorMessage}</div>}

      {/* Final Download Button */}
      {generationStage === 'Ready' && downloadUrl && (
        <button className="download-btn" onClick={onDownload}>
          📥 Download BeamNG Mod ZIP
        </button>
      )}
    </div>
  );
};
