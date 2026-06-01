import os
from urllib.parse import urlparse


def looks_like_supabase(s: str) -> bool:
    if not s:
        return False
    s = s.lower()
    try:
        p = urlparse(s)
        host = (p.hostname or '').lower()
        return 'supabase' in host
    except Exception:
        return False


if __name__ == '__main__':
    database_url = os.getenv('DATABASE_URL')

    if looks_like_supabase(database_url):
        print('Supabase detectado. Este servicio no modifica el esquema de la BD.')
    else:
        print('Advertencia: este entorno no es Supabase, pero igual no se ejecutan migraciones.')