import React, { useState, useEffect, useRef } from 'react';
import { MapViewer } from './components/MapViewer';
import { ControlPanel } from './components/ControlPanel';
import {
  MapSizeKey,
  MAP_SIZES,
  LocationSelection,
  GenerationStage,
} from './types';
import { requestMapGeneration, fetchJobStatus } from './api';

export const App: React.FC = () => {
  const [selectedLocation, setSelectedLocation] =
    useState<LocationSelection | null>(null);
  const [mapSize, setMapSize] = useState<MapSizeKey>('S');
  const [generationStage, setGenerationStage] =
    useState<GenerationStage>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [isIonTokenMissing, setIsIonTokenMissing] = useState<boolean>(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const pollTimerRef = useRef<number | null>(null);
  const extentMeters = MAP_SIZES[mapSize].extentMeters;

  // Cleanup polling timer on unmount
  useEffect(() => {
    return () => {
      if (pollTimerRef.current !== null) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  const stopPolling = () => {
    if (pollTimerRef.current !== null) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  const handleSelectLocation = (loc: LocationSelection) => {
    if (generationStage === 'idle' || generationStage === 'Ready' || generationStage === 'error') {
      setSelectedLocation(loc);
    }
  };

  const handleGenerate = async () => {
    if (!selectedLocation || activeJobId !== null) return;

    setErrorMessage(null);
    setDownloadUrl(null);
    setGenerationStage('Preparing area');

    const reqData = {
      latitude: selectedLocation.latitude,
      longitude: selectedLocation.longitude,
      size: mapSize,
      extentMeters: extentMeters,
    };

    try {
      const res = await requestMapGeneration(reqData);
      const jobId = res.jobId;
      setActiveJobId(jobId);

      // Poll job status at 500ms intervals
      stopPolling();
      pollTimerRef.current = window.setInterval(async () => {
        try {
          const jobStatus = await fetchJobStatus(jobId);

          if (jobStatus.status === 'completed') {
            stopPolling();
            setActiveJobId(null);
            setGenerationStage('Ready');
            setDownloadUrl(jobStatus.downloadUrl || `/api/jobs/${jobId}/download`);
          } else if (jobStatus.status === 'failed') {
            stopPolling();
            setActiveJobId(null);
            setGenerationStage('error');
            setErrorMessage(jobStatus.error || 'Map compilation failed');
          } else {
            // Update stage if valid stage string
            if (jobStatus.stage && jobStatus.stage !== 'failed') {
              setGenerationStage(jobStatus.stage as GenerationStage);
            }
          }
        } catch (err) {
          stopPolling();
          setActiveJobId(null);
          setGenerationStage('error');
          setErrorMessage(err instanceof Error ? err.message : 'Polling failed');
        }
      }, 500);
    } catch (err) {
      setActiveJobId(null);
      setGenerationStage('error');
      setErrorMessage(
        err instanceof Error ? err.message : 'Map generation initiation failed'
      );
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      const fullUrl = downloadUrl.startsWith('http')
        ? downloadUrl
        : `http://127.0.0.1:4317${downloadUrl}`;
      window.open(fullUrl, '_blank');
    }
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapViewer
        selectedLocation={selectedLocation}
        extentMeters={extentMeters}
        onSelectLocation={handleSelectLocation}
        onIonTokenMissing={setIsIonTokenMissing}
      />
      <ControlPanel
        selectedLocation={selectedLocation}
        mapSize={mapSize}
        generationStage={generationStage}
        errorMessage={errorMessage}
        downloadUrl={downloadUrl}
        isIonTokenMissing={isIonTokenMissing}
        onSelectMapSize={setMapSize}
        onGenerate={handleGenerate}
        onDownload={handleDownload}
      />
    </div>
  );
};
