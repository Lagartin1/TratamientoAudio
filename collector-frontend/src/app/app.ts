import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
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
  private snackBar = inject(MatSnackBar);
  private sanitizer = inject(DomSanitizer);

  archivoSeleccionado: File | null = null;
  audioUrl: SafeUrl | null = null; // enlace para el navegador
  latitud: number | null = null;
  longitud: number | null = null;
  enviando: boolean = false;



  // Si el usuario selecciona un audio
  seleccionarArchivo(event: Event) {
  const input = event.target as HTMLInputElement;
      if (input.files && input.files.length > 0) {
        this.actualizarArchivo(input.files[0]);
        this.snackBar.open('Archivo cargado con éxito', 'Cerrar', { duration: 3000 });
    }
  }

  //Si el usuario graba un audio
  manejarAudioGrabado(archivo: File) {
    this.actualizarArchivo(archivo);
    this.snackBar.open('Grabación lista. Capturando ubicación...', 'Cerrar', { duration: 2000 });
  }

  private actualizarArchivo(archivo: File) {
    // Si ya existía una URL previa, se libera
    this.archivoSeleccionado = null;
    this.audioUrl = null;

    setTimeout(() => {
      this.archivoSeleccionado = archivo;
      
      const urlTemporal = URL.createObjectURL(archivo);
      this.audioUrl = this.sanitizer.bypassSecurityTrustUrl(urlTemporal);
      
      this.obtenerUbicacion();
    }, 50);
    
  }

  //obtener ubicación automáticamente
  obtenerUbicacion() {
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
        this.snackBar.open('📍 Ubicación sincronizada con el audio.', 'Cerrar', { duration: 3000 });
      },
      (error) => {
        this.snackBar.open('⚠️ Error: Es obligatorio activar el GPS para enviar audios.', 'Cerrar', { duration: 5000 });
      },
      { enableHighAccuracy: true, timeout: 10000 } //alta precision
    );
  }

  enviarAudio() {
    if (!this.archivoSeleccionado) {
      this.snackBar.open('Por favor, selecciona o graba un audio primero.', 'Cerrar', { duration: 4000 });
      return;
    }
    if (!this.latitud || !this.longitud) {
      this.snackBar.open('Por favor, incluye tu ubicación.', 'Cerrar', { duration: 4000 });
      return;
    }

    this.enviando = true;
    
    //se envía el audio con la ubicacion
    console.log('Enviando a la API:', this.archivoSeleccionado, this.latitud, this.longitud);
    
  
    setTimeout(() => {
      this.snackBar.open('¡Audio enviado exitosamente para procesamiento!', 'Cerrar', { duration: 4000 });
      this.enviando = false;

      this.archivoSeleccionado = null;
      this.latitud = null;
      this.longitud = null;
    }, 2000);
  }

}