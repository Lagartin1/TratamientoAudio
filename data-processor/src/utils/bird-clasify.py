from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer
from datetime import datetime


class ClassifyBirds:
    def __init__(self, audio_file):
        self.audio_file = audio_file
        self.analyzer = Analyzer()
        self.results = []

    def classify(self):      
      recording = Recording(
          self.analyzer,
          self.audio_file,
          date=datetime(2026, 5, 18), # Opcional: ayuda a filtrar por época del año
          min_conf=0.70               # Confianza mínima (70%) para validar el ave
      )
      recording.analyze()
      self.results = list(recording.detections)
      
    def get_results(self):
        # lista simple con especie, nombre común, y confianza
        # merge las especies que son iguales en el arreglo de resultados
        species_dict = {}
        for detection in self.results:
            species = detection["scientific_name"]
            common_name = detection["common_name"]
            confidence = detection["confidence"]
            
            if species not in species_dict:
                species_dict[species] = {
                    "species": species,
                    "common_name": common_name,
                    "confidence": confidence
                }
            else:
                # Si ya existe la especie, actualizamos la confianza si es mayor
                if confidence > species_dict[species]["confidence"]:
                    species_dict[species]["confidence"] = confidence

        return list(species_dict.values())
      
# Ejemplo de uso
if __name__ == "__main__":
    audio_file = "../../test/queltehue.wav"
    classifier = ClassifyBirds(audio_file)
    classifier.classify()
    results = classifier.get_results()
    print(results)