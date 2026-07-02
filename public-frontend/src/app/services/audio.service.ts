import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map, tap, catchError } from 'rxjs/operators';
import { Audio } from '../models/audio.model';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class AudioService {

  private apiUrl = `${import.meta.env.NG_APP_API_URL}/api/audios`;

  constructor(private http: HttpClient, private auth: AuthService) { }

  // Los tags <audio> no envían el header Authorization, así que el token
  // va por query param para que el backend registre quién escuchó el audio.
  private streamUrl(audioId: string): string {
    const token = this.auth.getToken();
    const base = `${this.apiUrl}/${audioId}/stream`;
    return token ? `${base}?token=${encodeURIComponent(token)}` : base;
  }

  getAudios(): Observable<Audio[]> {
    return this.http.get<any>(this.apiUrl).pipe(
      map(respuesta => respuesta.data.map((item: any): Audio => ({
        id:             item.audio_id,
        latitud:        item.latitud,
        longitud:       item.longitud,
        decibels:       item.decibels,
        categoria:      item.audio_category,
        tipo_ave:       item.bird_name ?? undefined,
        audioStreamUrl: this.streamUrl(item.audio_id),
        duration:       item.duration ?? undefined,
        weather:        item.weather ?? undefined,
        createdAt:      item.created_at ?? undefined,
      }))),
      tap(audios => console.log(`✅ ${audios.length} audios recibidos:`, audios)),
      catchError(err => { console.error('❌ Error al recibir audios:', err); throw err; })
    );
  }
}
