import { Component, inject, ChangeDetectorRef, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AudioRecorder } from './components/audio-recorder/audio-recorder';

@Component({
  selector: 'app-root',
  imports: [
    CommonModule,
    MatButtonModule,
    MatCardModule,
    MatSnackBarModule,
    AudioRecorder
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  @ViewChild('audioPlayer') audioPlayer!: ElementRef<HTMLAudioElement>;

  private snackBar = inject(MatSnackBar);
  private cdr = inject(ChangeDetectorRef);

  archivoSeleccionado: File | null = null;
  audioUrl: string | null = null;
  latitud: number | null = null;
  longitud: number | null = null;
  enviando: boolean = false;

  seleccionarArchivo(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.actualizarArchivo(input.files[0]);
      this.snackBar.open('Archivo cargado con éxito', 'Cerrar', { duration: 3000 });
    }
  }

  manejarAudioGrabado(archivo: File) {
    this.actualizarArchivo(archivo);
  }

  private actualizarArchivo(archivo: File) {
    this.archivoSeleccionado = null;
    this.audioUrl = null;
    this.cdr.detectChanges();

    Promise.resolve().then(() => {
      this.archivoSeleccionado = archivo;
      this.audioUrl = URL.createObjectURL(archivo);
      this.cdr.detectChanges();

      Promise.resolve().then(() => {
        const audio = this.audioPlayer?.nativeElement;
        if (!audio) return;

        audio.load();
        audio.onloadedmetadata = () => {
          audio.onloadedmetadata = null;
          if (audio.duration === Infinity || isNaN(audio.duration)) {
            audio.currentTime = 1e101;
            audio.ontimeupdate = () => {
              audio.ontimeupdate = null;
              audio.currentTime = 0;
            };
          }
        };
      });
    });
  }

  private obtenerUbicacion(callback: () => void) {
    this.latitud = null;
    this.longitud = null;

    if (!navigator.geolocation) {
      this.snackBar.open('Tu dispositivo no soporta geolocalización.', 'Cerrar', { duration: 4000 });
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        this.latitud = position.coords.latitude;
        this.longitud = position.coords.longitude;
        this.cdr.detectChanges();
        callback();
      },
      () => {
        this.snackBar.open('⚠️ Error: Es obligatorio activar el GPS para enviar audios.', 'Cerrar', { duration: 5000 });
        this.enviando = false;
        this.cdr.detectChanges();

      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }

  enviarAudio() {
    if (!this.archivoSeleccionado) {
      this.snackBar.open('Por favor, selecciona o graba un audio primero.', 'Cerrar', { duration: 4000 });
      return;
    }

    this.enviando = true;
    this.snackBar.open('Obteniendo ubicación...', 'Cerrar', { duration: 2000 });

    this.obtenerUbicacion(() => {
      const formData = new FormData();
      formData.append('audio', this.archivoSeleccionado!, this.archivoSeleccionado!.name);
      formData.append('latitude', this.latitud!.toString());
      formData.append('longitude', this.longitud!.toString());
      formData.append('device_model', navigator.userAgent);

      fetch(`${import.meta.env['NG_APP_URL_COLLECTOR_API']}/api/upload-audio`, {
        method: 'POST',
        body: formData
      })
        .then(response => {
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          return response.json();
        })
        .then(() => {
          this.snackBar.open('¡Audio enviado exitosamente!', 'Cerrar', { duration: 4000 });
          this.archivoSeleccionado = null;
          this.audioUrl = null;
          this.latitud = null;
          this.longitud = null;
        })
        .catch(err => {
          console.error('Error al enviar audio:', err);
          this.snackBar.open('Error al enviar el audio. Intenta nuevamente.', 'Cerrar', { duration: 5000 });
        })
        .finally(() => {
          this.enviando = false;
          this.cdr.detectChanges();
        });
    });
  }
}