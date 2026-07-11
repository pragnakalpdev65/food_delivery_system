# apps/core/middleware/jwt_auth.py

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models.user import CustomUser

logger = logging.getLogger(__name__)


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        try:
            query_string = parse_qs(scope["query_string"].decode())
            token = query_string.get("token")

            if token:
                access_token = AccessToken(token[0])
                user = await self.get_user(access_token["user_id"])
                scope["user"] = user

        except Exception:
            # Invalid/expired token → keep AnonymousUser; consumers close with 4401.
            logger.debug("WebSocket JWT auth failed", exc_info=True)

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return AnonymousUser()
