from django.db import models

from forge_core.models import SoftDeleteModel, TimeStampedModel, UUIDModel


class Stamped(TimeStampedModel):
    name = models.CharField(max_length=20, default="x")


class Identified(UUIDModel):
    name = models.CharField(max_length=20, default="x")


class Document(UUIDModel, TimeStampedModel, SoftDeleteModel):
    title = models.CharField(max_length=50)
