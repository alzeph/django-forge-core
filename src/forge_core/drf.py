"""
Intégration Django REST Framework (extra `drf`).

    from forge_core.drf import respond

    class ArticleView(APIView):
        def get(self, request, pk):
            return respond(get_article(pk))

Dans `settings.py`, pour que toute `ForgeError` levée dans une vue devienne une
réponse JSON propre :

    REST_FRAMEWORK = {"EXCEPTION_HANDLER": "forge_core.drf.exception_handler"}
"""

from __future__ import annotations

from typing import Any

from pycatch import Err, Ok
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from forge_core.errors import ForgeError


def error_response(error: ForgeError) -> Response:
    """Réponse JSON `{"code": ..., "detail": ...}` avec le statut de l'erreur."""
    return Response(error.as_dict(), status=error.status)


def respond(result: Any, status: int = 200) -> Response:
    """Convertit un `Result` pycatch en réponse HTTP.

    - `Ok(valeur)` : `valeur` avec le statut `status` ;
    - `Err(ForgeError)` : réponse d'erreur correspondante ;
    - `Err(autre exception)` : l'exception est relevée (erreur de programmation).
    """
    match result:
        case Ok(value):
            return Response(value, status=status)
        case Err(ForgeError() as error):
            return error_response(error)
        case Err(error):
            raise error
    raise TypeError(f"Result pycatch attendu, reçu {type(result).__name__}")


def exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Gestionnaire DRF : traite `ForgeError`, délègue le reste à DRF."""
    if isinstance(exc, ForgeError):
        return error_response(exc)
    return drf_exception_handler(exc, context)
