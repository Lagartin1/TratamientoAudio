import { Component, EventEmitter, Output, inject, ChangeDetectorRef } from '@angular/core';
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

  estaGrabando = false;
  
  private preparando = false;   
  private workletCargado = false;
  private cdr = inject(ChangeDetectorRef);

  private audioCtx!: AudioContext;
  private source!: MediaStreamAudioSourceNode;
  private workletNode!: AudioWorkletNode;
  private stream!: MediaStream;
  private bufferMuestras: Float32Array[] = [];
  private numCanales = 1;

  async grabarAudio() {
    console.log('CLIC grabar | estaGrabando:', this.estaGrabando, '| preparando:', this.preparando, '| ctx state:', this.audioCtx?.state);

    if (this.estaGrabando || this.preparando) return;
    this.preparando = true;

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.bufferMuestras = [];

      if (!this.audioCtx) {
        this.audioCtx = new AudioContext();
      }

      if (this.audioCtx.state === 'suspended') {
        await this.audioCtx.resume();
      }

      if (!this.workletCargado) {
        await this.audioCtx.audioWorklet.addModule('/recorder-processor.js');
        this.workletCargado = true;
      }

      this.source = this.audioCtx.createMediaStreamSource(this.stream);
      this.workletNode = new AudioWorkletNode(this.audioCtx, 'recorder-processor');

      this.workletNode.port.onmessage = (event) => {
        if (event.data?.debug) {
          console.log('CANALES:', event.data.canales, '| TAM BLOQUE:', event.data.tam);
          return;
        }
        if (!this.estaGrabando) return;
        this.bufferMuestras.push(new Float32Array(event.data));
      };

      const silencio = this.audioCtx.createGain();
      silencio.gain.value = 0;

      this.source.connect(this.workletNode);
      this.workletNode.connect(silencio);
      silencio.connect(this.audioCtx.destination);

      this.estaGrabando = true;
      this.cdr.detectChanges();
    } catch (err) {
      console.error('No se pudo acceder al micrófono', err);
    } finally {
      this.preparando = false;
    }
  }

  detenerGrabacion() {
    if (!this.estaGrabando) return;
    this.estaGrabando = false;
    this.cdr.detectChanges();

    const sampleRateReal = this.audioCtx.sampleRate;

    this.workletNode.port.onmessage = null;
    this.workletNode.disconnect();
    this.source.disconnect();
    this.stream.getTracks().forEach(track => track.stop());

    const muestras = this.unirBuffers(this.bufferMuestras);
    this.bufferMuestras = [];

    console.log('sampleRate:', sampleRateReal, '| muestras:', muestras.length, '| duración estimada:', muestras.length / sampleRateReal, 's');

    const wavBlob = this.codificarWav(muestras, sampleRateReal, this.numCanales);

    const nombreArchivo = `grabacion_${Date.now()}.wav`;
    const audioFile = new File([wavBlob], nombreArchivo, { type: 'audio/wav' });
    this.audioGrabado.emit(audioFile);
  }

  private unirBuffers(trozos: Float32Array[]): Float32Array {
    let largoTotal = 0;
    for (const t of trozos) largoTotal += t.length;
    const resultado = new Float32Array(largoTotal);
    let offset = 0;
    for (const t of trozos) {
      resultado.set(t, offset);
      offset += t.length;
    }
    return resultado;
  }

  private codificarWav(muestras: Float32Array, sampleRate: number, numCanales: number): Blob {
    const longitudDatos = muestras.length * 2;
    const arrayBuffer = new ArrayBuffer(44 + longitudDatos);
    const vista = new DataView(arrayBuffer);

    const escribirTexto = (offset: number, texto: string) => {
      for (let i = 0; i < texto.length; i++) {
        vista.setUint8(offset + i, texto.charCodeAt(i));
      }
    };

    let offset = 0;
    escribirTexto(offset, 'RIFF'); offset += 4;
    vista.setUint32(offset, 36 + longitudDatos, true); offset += 4;
    escribirTexto(offset, 'WAVE'); offset += 4;
    escribirTexto(offset, 'fmt '); offset += 4;
    vista.setUint32(offset, 16, true); offset += 4;
    vista.setUint16(offset, 1, true); offset += 2;
    vista.setUint16(offset, numCanales, true); offset += 2;
    vista.setUint32(offset, sampleRate, true); offset += 4;
    vista.setUint32(offset, sampleRate * numCanales * 2, true); offset += 4;
    vista.setUint16(offset, numCanales * 2, true); offset += 2;
    vista.setUint16(offset, 16, true); offset += 2;
    escribirTexto(offset, 'data'); offset += 4;
    vista.setUint32(offset, longitudDatos, true); offset += 4;

    let pos = 44;
    for (let i = 0; i < muestras.length; i++) {
      let m = Math.max(-1, Math.min(1, muestras[i]));
      m = m < 0 ? m * 0x8000 : m * 0x7fff;
      vista.setInt16(pos, m, true);
      pos += 2;
    }

    return new Blob([arrayBuffer], { type: 'audio/wav' });
  }
}