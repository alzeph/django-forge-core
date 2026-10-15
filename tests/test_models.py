import uuid

import pytest

from tests.testapp.models import Document, Identified, Stamped

pytestmark = pytest.mark.django_db


class TestTimeStamped:
    def test_created_and_updated_are_set(self):
        obj = Stamped.objects.create()
        assert obj.created_at and obj.updated_at

    def test_updated_at_changes_created_at_does_not(self):
        obj = Stamped.objects.create()
        created, updated = obj.created_at, obj.updated_at
        obj.name = "y"
        obj.save()
        obj.refresh_from_db()
        assert obj.created_at == created
        assert obj.updated_at >= updated


class TestUUID:
    def test_primary_key_is_uuid4(self):
        obj = Identified.objects.create()
        assert isinstance(obj.pk, uuid.UUID) and obj.pk.version == 4

    def test_keys_are_unique(self):
        assert Identified.objects.create().pk != Identified.objects.create().pk


class TestSoftDelete:
    def test_delete_is_logical(self):
        doc = Document.objects.create(title="a")
        doc.delete()
        assert doc.is_deleted
        assert Document.objects.count() == 0
        assert Document.all_objects.count() == 1

    def test_delete_returns_count(self):
        doc = Document.objects.create(title="a")
        assert doc.delete()[0] == 1

    def test_restore(self):
        doc = Document.objects.create(title="a")
        doc.delete()
        doc.restore()
        assert not doc.is_deleted
        assert Document.objects.count() == 1

    def test_hard_delete(self):
        doc = Document.objects.create(title="a")
        doc.hard_delete()
        assert Document.all_objects.count() == 0

    def test_queryset_delete_is_logical(self):
        Document.objects.create(title="a")
        Document.objects.create(title="b")
        count, detail = Document.objects.all().delete()
        assert count == 2 and detail == {"testapp.Document": 2}
        assert Document.all_objects.count() == 2
        assert Document.objects.count() == 0

    def test_queryset_hard_delete(self):
        Document.objects.create(title="a")
        Document.all_objects.all().hard_delete()
        assert Document.all_objects.count() == 0

    def test_alive_and_dead_filters(self):
        Document.objects.create(title="alive")
        Document.objects.create(title="dead").delete()
        assert [d.title for d in Document.all_objects.alive()] == ["alive"]
        assert [d.title for d in Document.all_objects.dead()] == ["dead"]

    def test_delete_does_not_touch_other_fields(self):
        doc = Document.objects.create(title="a")
        doc.delete()
        doc.refresh_from_db()
        assert Document.all_objects.get(pk=doc.pk).title == "a"
