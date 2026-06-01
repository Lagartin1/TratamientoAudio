import { Injectable } from '@angular/core';
import * as L from 'leaflet';
import 'leaflet.heat';
import { Audio } from '../models/audio.model';
import { buildMarkerIcon } from '../components/noise-map/utils/marker-icons';
import { buildPopupTemplate } from '../components/noise-map/utils/popup-template';

@Injectable({
  providedIn: 'root'
})
export class MapRendererService {

  buildHeatLayer(audios: Audio[]): L.Layer {
    const puntos = audios.map(a => [
      a.latitud,
      a.longitud,
      a.decibels / 100
    ] as [number, number, number]);

    return L.heatLayer(puntos, {
      radius: 30,
      blur: 30,
      maxZoom: 17,
      gradient: {
        0.2: '#10b981',
        0.5: '#f59e0b',
        0.8: '#ef4444'
      }
    });
  }

  buildPinesLayer(audios: Audio[]): L.LayerGroup {
    const grupo = L.layerGroup();

    audios.forEach(audio => {
      const icono = buildMarkerIcon();
      const popup = buildPopupTemplate(audio);

      L.marker([audio.latitud, audio.longitud], { icon: icono })
        .bindPopup(popup)
        .addTo(grupo);
    });

    return grupo;
  }
}