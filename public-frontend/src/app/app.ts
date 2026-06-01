import { Component } from '@angular/core';
import { NoiseMapComponent } from './components/noise-map/noise-map';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [NoiseMapComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class AppComponent {
  title = 'public-frontend';
  
  // Estado inicial: el mapa de ruido parte seleccionado
  mostrarMapaRuido: boolean = true;

  // Función para cambiar el estado al hacer clic en el checkbox
  toggleMapaRuido() {
    this.mostrarMapaRuido = !this.mostrarMapaRuido;
    console.log('¿Mostrar mapa de ruido?:', this.mostrarMapaRuido);
  }
}