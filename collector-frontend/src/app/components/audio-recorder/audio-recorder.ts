import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-audio-recorder',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './audio-recorder.html',
  styleUrl: './audio-recorder.css'
})
export class AudioRecorder {
  @Output() audioGrabado = new EventEmitter<File>();

  mediaRecorder!: MediaRecorder;
  audioChunks: Blob[] = [];
  estaGrabando = false;

  grabarAudio() {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then((stream) => {
        this.audioChunks = [];
        this.mediaRecorder = new MediaRecorder(stream);
        this.mediaRecorder.start();
        this.estaGrabando = true;

        this.mediaRecorder.ondataavailable = (event) => {
          this.audioChunks.push(event.data);
        };

        this.mediaRecorder.onstop = () => {
          this.estaGrabando = false;

          const tipoMime = this.mediaRecorder.mimeType || 'audio/webm';
          
          const extension = tipoMime.split(';')[0].split('/')[1] || 'webm';

          const audioBlob = new Blob(this.audioChunks, { type: tipoMime });
          
          const nombreArchivo = `grabacion_${Date.now()}.${extension}`;
          const audioFile = new File([audioBlob], nombreArchivo, { type: tipoMime });

          this.audioGrabado.emit(audioFile);
        };
      })
      .catch(err => {
        console.error('No se pudo acceder al micrófono', err);
      });
  }

  detenerGrabacion() {
    if (this.mediaRecorder && this.estaGrabando) {
      this.mediaRecorder.stop();
    }
  }
}