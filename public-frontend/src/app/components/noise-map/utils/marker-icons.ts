import * as L from 'leaflet';

interface MarkerConfig {
  colorPrincipal: string;
  sombra: string;
}

function getMarkerConfig(): MarkerConfig {
  return {
    colorPrincipal: '#ef4444',
    sombra: 'rgba(239, 68, 68, 0.28)'
  };
}

export function buildMarkerIcon(): L.DivIcon {
  const { colorPrincipal, sombra } = getMarkerConfig();

  return L.divIcon({
    html: `
      <div class="sound-marker" style="--marker-color: ${colorPrincipal}; --marker-shadow: ${sombra};">
        <div class="sound-marker__shape"></div>
      </div>
    `,
    className: 'soundcolab-map-marker',
    iconSize: [36, 40],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36]
  });
}