"""
Configuration par l'environnement.

Lecture typée des variables d'environnement pour `settings.py`, et fusion de
couches de configuration (base, dev, prod).

    from forge_core.conf import env, env_bool, env_list, deep_merge, current_environment

    SECRET_KEY = env("SECRET_KEY")
    DEBUG = env_bool("DEBUG", default=False)
    ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", default=["localhost"])

Une variable absente sans valeur par défaut lève `ImproperlyConfigured` avec le
nom de la variable, au lieu d'une erreur obscure plus tard.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from django.core.exceptions import ImproperlyConfigured

_MISSING: Any = object()
_TRUE = {"1", "true", "yes", "on", "oui"}
_FALSE = {"0", "false", "no", "off", "non", ""}

ENVIRONMENT_VARIABLE = "FORGE_ENV"
DEFAULT_ENVIRONMENT = "dev"


def env[T](name: str, default: Any = _MISSING, cast: Callable[[str], T] = str) -> T:  # type: ignore[assignment]
    """Valeur de la variable `name`, convertie avec `cast`.

    `default` est retourné tel quel (sans conversion) si la variable est absente.
    """
    raw = os.environ.get(name)
    if raw is None:
        if default is _MISSING:
            raise ImproperlyConfigured(f"Variable d'environnement requise : {name}")
        return default
    try:
        return cast(raw)
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(f"Valeur invalide pour {name} : {raw!r} ({exc})") from exc


def env_bool(name: str, default: Any = _MISSING) -> bool:
    """Booléen : `1/true/yes/on/oui` ou `0/false/no/off/non` (insensible à la casse)."""
    return env(name, default, cast=_to_bool)


def env_int(name: str, default: Any = _MISSING) -> int:
    """Entier."""
    return env(name, default, cast=int)


def env_float(name: str, default: Any = _MISSING) -> float:
    """Nombre décimal."""
    return env(name, default, cast=float)


def env_list(name: str, default: Any = _MISSING, sep: str = ",") -> list[str]:
    """Liste de chaînes séparées par `sep`, sans espaces ni éléments vides."""
    return env(name, default, cast=lambda raw: _to_list(raw, sep))


def current_environment() -> str:
    """Nom de l'environnement courant (`FORGE_ENV`, `dev` par défaut)."""
    return os.environ.get(ENVIRONMENT_VARIABLE, DEFAULT_ENVIRONMENT).strip().lower()


def deep_merge(*layers: Mapping[str, Any]) -> dict[str, Any]:
    """Fusionne des dictionnaires de gauche à droite ; la dernière couche l'emporte.

    Les dictionnaires imbriqués sont fusionnés récursivement (utile pour
    `LOGGING` ou `DATABASES`) ; les autres valeurs, listes comprises, sont remplacées.
    Les arguments ne sont pas modifiés.
    """
    merged: dict[str, Any] = {}
    for layer in layers:
        for key, value in layer.items():
            if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
                merged[key] = deep_merge(merged[key], value)
            elif isinstance(value, Mapping):
                merged[key] = deep_merge(value)
            else:
                merged[key] = value
    return merged


def _to_bool(raw: str) -> bool:
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise ValueError("booléen attendu (true/false)")


def _to_list(raw: str, sep: str) -> list[str]:
    items: Sequence[str] = raw.split(sep)
    return [item.strip() for item in items if item.strip()]
