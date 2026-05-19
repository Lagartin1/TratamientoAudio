import librosa
import numpy as np
import os

class SoundSpecsClassifier:
    def __init__(self, audio_file):
        """
        Inicializa el clasificador con la ruta del archivo de audio.
        """
        self.audio_file = audio_file
        if not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"El archivo {self.audio_file} no existe.")
            
        # Cargamos el audio usando librosa
        self.y, self.sr = librosa.load(audio_file, sr=None)

    def get_decibels(self):
        """
        Calcula los decibeles (dBFS) promedio del audio basándose en la energía RMS.
        """
        rms = librosa.feature.rms(y=self.y)[0]
        # Filtramos valores muy cercanos a cero para evitar log(0)
        rms = rms[rms > 1e-10]
        if len(rms) > 0:
            db = 20 * np.log10(rms)
            return float(np.mean(db))
        return -100.0  # Silencio total

    def get_noise_type(self):
        """
        Clasifica el tipo de ruido basándose en la planicidad espectral y el centroide.
        """
        # Flatness espectral (cercano a 1 es ruido blanco, cercano a 0 es tonal)
        flatness = np.mean(librosa.feature.spectral_flatness(y=self.y))
        
        # Centroide espectral ("centro de masa" de las frecuencias)
        centroid = np.mean(librosa.feature.spectral_centroid(y=self.y, sr=self.sr))

        if flatness > 0.05:
            return "Ruido Blanco / Banda Ancha"
        elif centroid < 1000:
            return "Graves / Retumbo (Baja Frecuencia)"
        elif centroid > 4000:
            return "Agudos / Siseo (Alta Frecuencia)"
        else:
            return "Tonal / Rango Medio"

    def classify(self):
        """
        Retorna un diccionario con las especificaciones calculadas.
        """
        return {
            "decibels": self.get_decibels(),
            "noise_type": self.get_noise_type(),
            "sample_rate": self.sr
        }

if __name__ == "__main__":
    # Prueba rápida usando el archivo queltehue.wav local
    test_file = "queltehue.wav"
    try:
        classifier = SoundSpecsClassifier(test_file)
        results = classifier.classify()
        print(f"Resultados para {test_file}:")
        print(f"Decibeles (dBFS): {results['decibels']:.2f} dB")
        print(f"Tipo de ruido: {results['noise_type']}")
        print(f"Tasa de muestreo: {results['sample_rate']} Hz")
    except Exception as e:
        print(f"Error: {e}")
