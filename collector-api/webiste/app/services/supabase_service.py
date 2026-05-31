from supabase import Client, create_client


class SupabaseService:
    def __init__(self, url=None, key=None):
        self.url = url
        self.key = key
        self._client = None

    @property
    def client(self) -> Client:
        if not self.url or not self.key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be configured")

        if self._client is None:
            self._client = create_client(self.url, self.key)
        return self._client

    def get_user_from_token(self, token):
        response = self.client.auth.get_user(token)
        return response.user


def get_supabase_service(app):
    return SupabaseService(
        url=app.config.get("SUPABASE_URL"),
        key=app.config.get("SUPABASE_KEY"),
    )
