"""
Modèles abstraits communs.

    from forge_core.models import TimeStampedModel, UUIDModel, SoftDeleteModel

    class Article(UUIDModel, TimeStampedModel, SoftDeleteModel):
        title = models.CharField(max_length=200)

Ces classes sont abstraites : `forge_core` n'a pas besoin d'être dans
`INSTALLED_APPS`, et elles ne créent aucune migration propre.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Ajoute `created_at` (à la création) et `updated_at` (à chaque sauvegarde)."""

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Clé primaire `id` de type UUID4."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet dont `delete()` marque les lignes au lieu de les supprimer."""

    def delete(self) -> tuple[int, dict[str, int]]:  # type: ignore[override]
        count = self.update(deleted_at=timezone.now())
        return count, {self.model._meta.label: count}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        return super().delete()

    def alive(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):  # type: ignore[misc]
    """Manager par défaut : ne retourne que les lignes non supprimées."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(models.Model):
    """Suppression logique : `delete()` renseigne `deleted_at`.

    - `objects` ne voit que les lignes actives ;
    - `all_objects` voit tout ;
    - `restore()` annule la suppression, `hard_delete()` supprime pour de bon.
    """

    deleted_at = models.DateTimeField(null=True, blank=True, editable=False, db_index=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:  # type: ignore[override]
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
        return 1, {self._meta.label: 1}

    def restore(self) -> None:
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    def hard_delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        return super().delete(*args, **kwargs)
