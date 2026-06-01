import { Component, OnInit, Input, inject, OnDestroy, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';
import { AudioService } from '../../services/audio.service';
import { MapRendererService } from '../../services/map-renderer.service';

@Component({
  selector: 'app-noise-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './noise-map.html',
  styleUrls: ['./noise-map.css']
})
export class NoiseMapComponent implements OnInit, AfterViewInit, OnDestroy {
  private map!: L.Map;
  private resizeObserver?: ResizeObserver;
  private capaCalor?: L.Layer;
  private capaPines?: L.LayerGroup;

  private audioService = inject(AudioService);
  private mapRenderer = inject(MapRendererService);

  @Input() set capaActiva(valor: boolean) {
    this._capaActiva = valor;
    this.aplicarFiltroRuido();
  }
  get capaActiva(): boolean {
    return this._capaActiva;
  }
  private _capaActiva: boolean = true;

  ngOnInit() {
    this.audioService.getAudios().subscribe({
      next: (audios) => {
        this.capaCalor = this.mapRenderer.buildHeatLayer(audios);
        this.capaPines = this.mapRenderer.buildPinesLayer(audios);

        if (this.map) {
          this.aplicarFiltroRuido();
        }
      },
      error: (err) => console.error('Error al cargar audios:', err)
    });
  }

  ngAfterViewInit() {
    setTimeout(() => this.inicializarMapa(), 150);
  }

  private inicializarMapa() {
    this.map = L.map('mapa-ruido-uach', {
      zoom: 17,
      center: L.latLng(-39.833464, -73.246310),
      fadeAnimation: true
    });

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri'
    }).addTo(this.map);

    this.map.invalidateSize();

    this.map.on('viewreset moveend zoomend', () => this.map.invalidateSize());

    this.resizeObserver = new ResizeObserver(() => this.map?.invalidateSize());
    this.resizeObserver.observe(this.map.getContainer());

    if (this.capaPines) {
      this.aplicarFiltroRuido();
    }
  }

  private aplicarFiltroRuido() {
    if (!this.map || !this.capaCalor || !this.capaPines) return;

    if (this.capaActiva) {
      if (!this.map.hasLayer(this.capaCalor)) this.map.addLayer(this.capaCalor);
      if (!this.map.hasLayer(this.capaPines)) this.map.addLayer(this.capaPines);
    } else {
      if (this.map.hasLayer(this.capaCalor)) this.map.removeLayer(this.capaCalor);
      if (!this.map.hasLayer(this.capaPines)) this.map.addLayer(this.capaPines);
    }
  }

  ngOnDestroy() {
    this.resizeObserver?.disconnect();
    if (this.map) {
      this.map.off();
      this.map.remove();
    }
  }
}