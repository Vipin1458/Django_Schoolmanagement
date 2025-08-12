# chat/middleware.py
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        user_id = access_token["user_id"]
        return User.objects.get(id=user_id)
    except Exception:
        return None

class JWTAuthMiddleware:
    """Custom JWT auth middleware for Django Channels."""
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Parse query params
        query_params = parse_qs(scope["query_string"].decode())
        token_list = query_params.get("token")
        if token_list:
            token = token_list[0]
            user = await get_user_from_token(token)
            scope["user"] = user or None
        else:
            scope["user"] = None

        return await self.inner(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    from channels.auth import AuthMiddlewareStack
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))
