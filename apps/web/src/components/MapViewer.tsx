import React, { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import { LocationSelection } from '../types';

interface MapViewerProps {
  selectedLocation: LocationSelection | null;
  extentMeters: number;
  onSelectLocation: (loc: LocationSelection) => void;
  onIonTokenMissing: (missing: boolean) => void;
}

export const MapViewer: React.FC<MapViewerProps> = ({
  selectedLocation,
  extentMeters,
  onSelectLocation,
  onIonTokenMissing,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Cesium.Viewer | null>(null);
  const selectionEntityRef = useRef<Cesium.Entity | null>(null);

  // Initialize Cesium Viewer
  useEffect(() => {
    if (!containerRef.current) return;

    const ionToken = import.meta.env.VITE_CESIUM_ION_TOKEN;
    if (ionToken) {
      Cesium.Ion.defaultAccessToken = ionToken;
      onIonTokenMissing(false);
    } else {
      Cesium.Ion.defaultAccessToken = '';
      onIonTokenMissing(true);
    }

    const osmProvider = new Cesium.OpenStreetMapImageryProvider({
      url: 'https://tile.openstreetmap.org/',
    });

    const viewer = new Cesium.Viewer(containerRef.current, {
      animation: false,
      timeline: false,
      navigationHelpButton: false,
      sceneModePicker: false,
      homeButton: false,
      geocoder: false,
      baseLayerPicker: false,
      fullscreenButton: false,
      infoBox: false,
      selectionIndicator: false,
      baseLayer: ionToken ? undefined : new Cesium.ImageryLayer(osmProvider),
      terrainProvider: new Cesium.EllipsoidTerrainProvider(),
    });

    viewerRef.current = viewer;

    // Set camera view over Central Europe (Slovakia: lon 18.3, lat 48.7, height 900,000m)
    viewer.camera.setView({
      destination: Cesium.Cartesian3.fromDegrees(18.3, 48.7, 900000),
    });

    // Map Click Listener
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((click: { position: Cesium.Cartesian2 }) => {
      const ray = viewer.camera.getPickRay(click.position);
      if (!ray) return;
      const cartesian = viewer.scene.globe.pick(ray, viewer.scene);
      if (!cartesian) return;

      const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
      const lat = Cesium.Math.toDegrees(cartographic.latitude);
      const lon = Cesium.Math.toDegrees(cartographic.longitude);

      onSelectLocation({
        latitude: parseFloat(lat.toFixed(6)),
        longitude: parseFloat(lon.toFixed(6)),
      });
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    return () => {
      handler.destroy();
      if (!viewer.isDestroyed()) {
        viewer.destroy();
      }
    };
  }, []);

  // Update selection overlay rectangle whenever selected location or extent changes
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    if (selectionEntityRef.current) {
      viewer.entities.remove(selectionEntityRef.current);
      selectionEntityRef.current = null;
    }

    if (!selectedLocation) return;

    const halfExtent = extentMeters / 2;
    const latRad = (selectedLocation.latitude * Math.PI) / 180;

    const deltaLat = halfExtent / 111320;
    const deltaLon = halfExtent / (111320 * Math.cos(latRad));

    const south = selectedLocation.latitude - deltaLat;
    const north = selectedLocation.latitude + deltaLat;
    const west = selectedLocation.longitude - deltaLon;
    const east = selectedLocation.longitude + deltaLon;

    const rectangle = Cesium.Rectangle.fromDegrees(west, south, east, north);

    const entity = viewer.entities.add({
      rectangle: {
        coordinates: rectangle,
        material: Cesium.Color.fromCssColorString('#00e5ff').withAlpha(0.25),
        outline: true,
        outlineColor: Cesium.Color.fromCssColorString('#00e5ff'),
        outlineWidth: 3,
        height: 0,
      },

      position: Cesium.Cartesian3.fromDegrees(
        selectedLocation.longitude,
        selectedLocation.latitude
      ),

      point: {
        pixelSize: 8,
        color: Cesium.Color.fromCssColorString('#00e5ff'),
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 2,
      },
    });

    selectionEntityRef.current = entity;

    // Smoothly fly camera to selected box if first selection
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(
        selectedLocation.longitude,
        selectedLocation.latitude,
        Math.max(extentMeters * 2.5, 1500)
      ),
      duration: 1.2,
    });
  }, [selectedLocation, extentMeters]);

  return (
    <div className="cesium-container-wrapper">
      <div ref={containerRef} className="cesium-viewer-wrapper" />
    </div>
  );
};
