# Instrucciones para ejecutar el backend y probar el endpoint de subida de audio

## 1. Instalar dependencias

Asegúrate de tener Python 3.10+ y pip instalados. Luego ejecuta:

```sh
pip install -r requirements.txt
```

## 2. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y asegúrate de que las variables de conexión a la base de datos estén correctas. Ejemplo:

```
SUPABASE_DB_URL=postgresql://postgres:Q7eX7ZfYqYv3BLGG@db.bbmkxrvvyxboiihylcdt.supabase.co:5432/postgres
POSTGRES_PW=Q7eX7ZfYqYv3BLGG
DATABASE_URL=postgresql://postgres:Q7eX7ZfYqYv3BLGG@db.bbmkxrvvyxboiihylcdt.supabase.co:5432/postgres
```


## 3. Inicializar la base de datos (**solo si NO tienes las tablas**)

Si es la primera vez y tu base de datos está vacía, puedes crear las tablas ejecutando en Python:

```python
from webiste.app.extensions import db
from bootstrap import create_app
app = create_app()
with app.app_context():
    db.create_all()
```

O usa un cliente SQL para ejecutar el script en `sql/init_schema.sql`.

**Si ya tienes la base de datos y las tablas creadas, puedes omitir este paso y continuar directamente con la ejecución del backend.**

## 4. Ejecutar el backend

```sh
python main.py
```

El backend quedará escuchando en `http://localhost:5000`.

## 5. Probar el endpoint

Puedes usar la extensión REST Client de VSCode o Postman. El archivo `upload_audio.http` contiene un ejemplo listo para usar.

- En VSCode, abre `upload_audio.http` y haz clic en `Send Request`.
- En Postman, crea una petición POST a `http://localhost:5000/api/upload-audio` con los campos y el archivo como en el ejemplo.

---

**Notas:**
- El usuario (`id_user`) debe existir previamente en la base de datos.
- El archivo de audio se almacena en la base de datos como binario.
- Si necesitas crear usuarios, usa el endpoint `/api/users` (ver código fuente).
