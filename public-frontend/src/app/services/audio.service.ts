import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { Audio } from '../models/audio.model';

@Injectable({
  providedIn: 'root'
})
export class AudioService {

  private apiUrl = `${import.meta.env.NG_APP_API_URL}/api/audios`;

  constructor(private http: HttpClient) { }

  getAudios(): Observable<Audio[]> {  
    return this.http.get<Audio[]>(this.apiUrl).pipe(
      tap(audios => console.log(`✅ ${audios.length} audios recibidos:`, audios)),
      catchError(err => { console.error('❌ Error al recibir audios:', err); throw err; })
    );
  }
}