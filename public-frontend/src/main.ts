import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app'; // O './app/app' según cómo se llame tu archivo en src/app/

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));