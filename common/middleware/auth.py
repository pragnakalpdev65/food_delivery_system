# apps/core/middleware/jwt_auth.py

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models.user import CustomUser

logger = logging.getLogger(__name__)


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        query_string = parse_qs(scope.get("query_string", b"").decode())
        token_list = query_string.get("token")

        if token_list:
            raw_token = token_list[0]
            try:
                access_token = AccessToken(raw_token)
                user = await self.get_user(access_token["user_id"])
                scope["user"] = user
                if not getattr(user, "is_authenticated", False):
                    logger.warning(
                        "WebSocket JWT valid but user %s not found",
                        access_token["user_id"],
                    )
            except (InvalidToken, TokenError) as exc:
                logger.warning("WebSocket JWT rejected: %s", exc)
            except Exception:
                logger.exception("WebSocket JWT auth failed unexpectedly")

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return AnonymousUser()
        except (TypeError, ValueError):
            return AnonymousUser()
