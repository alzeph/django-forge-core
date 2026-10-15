# django-forge-core

English | [Français](README.fr.md)

Runtime foundation for [Django Forge](https://github.com/alzeph/django-forge-cli) projects: small building blocks that generated code imports, also usable on their own in any Django project.

It provides three things:

- `settings.py` configuration read from the environment, with clear errors;
- common abstract models (timestamps, UUID, soft delete);
- typed business errors meant to be used with [pycatch](https://github.com/alzeph/pycatch) (`Result`), and their conversion into DRF responses.

## Installation

```bash
uv add django-forge-core
uv add "django-forge-core[drf]"   # with the Django REST Framework integration
```

Python 3.12 or later, Django 5.0 or later. Projects created with `forge init` get it through the Forge CLI.

## Configuration from the environment

```python
# settings.py
from forge_core.conf import env, env_bool, env_list, env_int, deep_merge, current_environment

SECRET_KEY = env("SECRET_KEY")                       # ImproperlyConfigured if missing
DEBUG = env_bool("DEBUG", default=False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", default=["localhost"])
DB_PORT = env_int("DB_PORT", default=5432)
```

| Function | Purpose |
|---|---|
| `env(name, default, cast)` | Value converted with `cast`; `default` is returned as is when the variable is missing |
| `env_bool` | `1/true/yes/on/oui` or `0/false/no/off/non` (case insensitive) |
| `env_int`, `env_float` | Numbers |
| `env_list(name, sep=",")` | List of strings, without spaces or empty items |
| `current_environment()` | Value of `FORGE_ENV` (`dev` by default) |
| `deep_merge(*layers)` | Merges configuration layers, nested dictionaries recursively |

A missing variable without a default raises `ImproperlyConfigured` naming the variable, and an invalid value reports both the name and the raw value.

Layers example:

```python
BASE = {"LOGGING": {"version": 1, "root": {"level": "INFO"}}}
PROD = {"LOGGING": {"root": {"level": "WARNING"}}}

layers = {"dev": BASE, "prod": deep_merge(BASE, PROD)}
globals().update(layers[current_environment()])
```

## Abstract models

```python
from django.db import models
from forge_core.models import SoftDeleteModel, TimeStampedModel, UUIDModel


class Article(UUIDModel, TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=200)
```

- `TimeStampedModel`: `created_at`, `updated_at`.
- `UUIDModel`: UUID4 primary key.
- `SoftDeleteModel`: `delete()` sets `deleted_at`. `Article.objects` only sees active rows, `Article.all_objects` sees everything. Methods `restore()` and `hard_delete()`, and on QuerySets `alive()`, `dead()`, `hard_delete()`.

These classes are abstract: no migration of their own, and `forge_core` does not need to be in `INSTALLED_APPS`.

## Typed errors and pycatch

```python
from pycatch import Err, Ok, Result
from forge_core.errors import NotFound


def get_article(pk: int) -> Result[Article, NotFound]:
    try:
        return Ok(Article.objects.get(pk=pk))
    except Article.DoesNotExist:
        return Err(NotFound(f"Article {pk} not found"))
```

Provided errors: `ValidationFailed` (400), `Unauthenticated` (401), `PermissionRefused` (403), `NotFound` (404), `Conflict` (409). Each carries a stable `code` and an HTTP `status`; `ForgeError` is the base class for your own.

## Django REST Framework

```python
from forge_core.drf import respond


class ArticleView(APIView):
    def get(self, request, pk):
        return respond(get_article(pk))
```

`respond` turns `Ok(value)` into a response and `Err(ForgeError)` into `{"code": ..., "detail": ...}` with the right status. So that a `ForgeError` raised inside a view produces the same response:

```python
REST_FRAMEWORK = {"EXCEPTION_HANDLER": "forge_core.drf.exception_handler"}
```

## Development

```bash
uv sync
uv run ruff check src tests
uv run pytest --cov=forge_core --cov-report=term-missing
```

## License

[MIT](LICENSE)
