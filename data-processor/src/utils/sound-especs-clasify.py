import librosa
import numpy as np
import os
import csv

class SoundSpecsClassifier:
    YAMNET_MODEL_URL = "https://tfhub.dev/google/yamnet/1"
    _yamnet_model = None
    _yamnet_class_names = None
    _tensorflow = None

    def __init__(self, audio_file):
        """
        Inicializa el clasificador con la ruta del archivo de audio.
        """
        self.audio_file = audio_file
        if not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"El archivo {self.audio_file} no existe.")
            
        # Cargamos el audio original para calcular especificaciones del archivo.
        self.y, self.sr = librosa.load(audio_file, sr=None)

    @classmethod
    def _load_yamnet(cls):
        """
        Carga YAMNet 1 desde TensorFlow Hub una sola vez por proceso.
        """
        if (
            cls._yamnet_model is not None
            and cls._yamnet_class_names is not None
            and cls._tensorflow is not None
        ):
            return cls._yamnet_model, cls._yamnet_class_names, cls._tensorflow

        try:
            import tensorflow as tf
            import tensorflow_hub as hub
        except ImportError as exc:
            raise ImportError(
                "YAMNet requiere tensorflow, tensorflow-hub y setuptools. "
                f"Ejecuta: pip install -r requirements.txt. Detalle: {exc}"
            ) from exc

        model = hub.load(cls.YAMNET_MODEL_URL)
        class_map_path = model.class_map_path().numpy().decode("utf-8")

        with open(class_map_path, newline="", encoding="utf-8") as class_map:
            reader = csv.DictReader(class_map)
            class_names = [row["display_name"] for row in reader]

        cls._yamnet_model = model
        cls._yamnet_class_names = class_names
        cls._tensorflow = tf
        return model, class_names, tf

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

    def get_duration(self):
        """
        Retorna la duracion del audio en segundos.
        """
        return float(librosa.get_duration(y=self.y, sr=self.sr))

    def get_avg_frequency(self):
        """
        Calcula la frecuencia promedio usando el centroide espectral.
        """
        centroid = librosa.feature.spectral_centroid(y=self.y, sr=self.sr)
        return float(np.mean(centroid))

    def get_noise_type(self):
        """
        Clasifica el sonido usando YAMNet 1.
        """
        prediction = self.get_yamnet_prediction()
        return prediction["label"]

    def get_yamnet_prediction(self, top_k=5):
        """
        Retorna la predicción principal de YAMNet y las mejores clases detectadas.
        """
        model, class_names, tf = self._load_yamnet()

        waveform, _ = librosa.load(self.audio_file, sr=16000, mono=True)
        waveform = tf.convert_to_tensor(waveform, dtype=tf.float32)

        scores, _embeddings, _spectrogram = model(waveform)
        mean_scores = np.mean(scores.numpy(), axis=0)
        top_indices = mean_scores.argsort()[-top_k:][::-1]

        top_predictions = [
            {
                "label": class_names[index],
                "confidence": float(mean_scores[index]),
            }
            for index in top_indices
        ]

        return {
            "label": top_predictions[0]["label"],
            "confidence": top_predictions[0]["confidence"],
            "top_predictions": top_predictions,
        }

    def classify(self):
        """
        Retorna un diccionario con las especificaciones calculadas.
        """
        yamnet_prediction = self.get_yamnet_prediction()
        return {
            "decibels": self.get_decibels(),
            "noise_type": yamnet_prediction["label"],
            "yamnet_confidence": yamnet_prediction["confidence"],
            "yamnet_top_predictions": yamnet_prediction["top_predictions"],
            "duration": self.get_duration(),
            "avg_frequency": self.get_avg_frequency(),
            "sample_rate": self.sr
        }

if __name__ == "__main__":
    # Prueba rápida usando el archivo queltehue.wav local
    test_file = "../../test/videoplayback.wav"
    try:
        classifier = SoundSpecsClassifier(test_file)
        results = classifier.classify()
        print(f"Resultados para {test_file}:")
        print(f"Decibeles (dBFS): {results['decibels']:.2f} dB")
        print(f"Tipo de ruido: {results['noise_type']}")
        print(f"Confianza YAMNet: {results['yamnet_confidence']:.4f}")
        print(f"Top predicciones YAMNet: {results['yamnet_top_predictions']}")
        print(f"Duracion: {results['duration']:.2f} s")
        print(f"Frecuencia promedio: {results['avg_frequency']:.2f} Hz")
        print(f"Tasa de muestreo: {results['sample_rate']} Hz")
    except Exception as e:
        print(f"Error: {e}")
