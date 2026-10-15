"""
Erreurs métier typées, à utiliser avec `pycatch`.

Une fonction de service annonce ses échecs dans sa signature au lieu de lever :

    from pycatch import Err, Ok, Result
    from forge_core.errors import NotFound

    def get_article(pk: int) -> Result[Article, NotFound]:
        try:
            return Ok(Article.objects.get(pk=pk))
        except Article.DoesNotExist:
            return Err(NotFound(f"Article {pk} introuvable"))

Chaque erreur porte un `code` stable (pour les clients) et un `status` HTTP
(utilisé par `forge_core.drf`).
"""

from __future__ import annotations

from typing import Any


class ForgeError(Exception):
    """Erreur métier de base."""

    code = "error"
    status = 400

    def __init__(self, detail: str = "", *, code: str | None = None, extra: Any = None) -> None:
        super().__init__(detail)
        self.detail = detail or self.code
        self.code = code or type(self).code
        self.extra = extra

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "detail": self.detail}
        if self.extra is not None:
            payload["extra"] = self.extra
        return payload


class ValidationFailed(ForgeError):
    code = "validation_failed"
    status = 400


class Unauthenticated(ForgeError):
    code = "unauthenticated"
    status = 401


class PermissionRefused(ForgeError):
    code = "permission_refused"
    status = 403


class NotFound(ForgeError):
    code = "not_found"
    status = 404


class Conflict(ForgeError):
    code = "conflict"
    status = 409
