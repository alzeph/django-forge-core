# django-forge-core

Socle runtime des projets [Django Forge](https://github.com/alzeph/django-forge-cli) : de petites briques que le code généré importe, utilisables aussi seules dans n'importe quel projet Django.

Il apporte trois choses :

- une configuration `settings.py` lue dans l'environnement, avec des erreurs claires ;
- des modèles abstraits courants (horodatage, UUID, suppression logique) ;
- des erreurs métier typées, à utiliser avec [pycatch](https://github.com/alzeph/pycatch) (`Result`), et leur conversion en réponses DRF.

## Installation

```bash
uv add django-forge-core
uv add "django-forge-core[drf]"   # avec l'intégration Django REST Framework
```

Python 3.12 ou plus, Django 5.0 ou plus.

## Configuration par l'environnement

```python
# settings.py
from forge_core.conf import env, env_bool, env_list, env_int, deep_merge, current_environment

SECRET_KEY = env("SECRET_KEY")                       # ImproperlyConfigured si absente
DEBUG = env_bool("DEBUG", default=False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", default=["localhost"])
DB_PORT = env_int("DB_PORT", default=5432)
```

| Fonction | Rôle |
|---|---|
| `env(name, default, cast)` | Valeur convertie avec `cast` ; `default` est rendu tel quel si la variable est absente |
| `env_bool` | `1/true/yes/on/oui` ou `0/false/no/off/non` |
| `env_int`, `env_float` | Nombres |
| `env_list(name, sep=",")` | Liste de chaînes, sans espaces ni éléments vides |
| `current_environment()` | Valeur de `FORGE_ENV` (`dev` par défaut) |
| `deep_merge(*layers)` | Fusionne des couches de configuration, les dictionnaires imbriqués récursivement |

Exemple de couches :

```python
BASE = {"LOGGING": {"version": 1, "root": {"level": "INFO"}}}
PROD = {"LOGGING": {"root": {"level": "WARNING"}}}

layers = {"dev": BASE, "prod": deep_merge(BASE, PROD)}
globals().update(layers[current_environment()])
```

## Modèles abstraits

```python
from django.db import models
from forge_core.models import SoftDeleteModel, TimeStampedModel, UUIDModel


class Article(UUIDModel, TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=200)
```

- `TimeStampedModel` : `created_at`, `updated_at`.
- `UUIDModel` : clé primaire UUID4.
- `SoftDeleteModel` : `delete()` renseigne `deleted_at`. `Article.objects` ne voit que les lignes actives, `Article.all_objects` voit tout. Méthodes `restore()` et `hard_delete()`, et sur les QuerySets `alive()`, `dead()`, `hard_delete()`.

Ces classes sont abstraites : pas de migration propre, et `forge_core` n'a pas besoin d'être dans `INSTALLED_APPS`.

## Erreurs typées et pycatch

```python
from pycatch import Err, Ok, Result
from forge_core.errors import NotFound


def get_article(pk: int) -> Result[Article, NotFound]:
    try:
        return Ok(Article.objects.get(pk=pk))
    except Article.DoesNotExist:
        return Err(NotFound(f"Article {pk} introuvable"))
```

Erreurs fournies : `ValidationFailed` (400), `Unauthenticated` (401), `PermissionRefused` (403), `NotFound` (404), `Conflict` (409). Chacune porte un `code` stable et un `status` HTTP ; `ForgeError` sert de base pour les vôtres.

## Django REST Framework

```python
from forge_core.drf import respond


class ArticleView(APIView):
    def get(self, request, pk):
        return respond(get_article(pk))
```

`respond` transforme `Ok(valeur)` en réponse et `Err(ForgeError)` en `{"code": ..., "detail": ...}` avec le bon statut. Pour qu'une `ForgeError` levée dans une vue produise la même réponse :

```python
REST_FRAMEWORK = {"EXCEPTION_HANDLER": "forge_core.drf.exception_handler"}
```

## Développement

```bash
uv sync
uv run ruff check src tests
uv run pytest --cov=forge_core --cov-report=term-missing
```

## Licence

[MIT](LICENSE)
