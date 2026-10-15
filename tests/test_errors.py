import pytest

from forge_core import errors


@pytest.mark.parametrize(
    ("cls", "code", "status"),
    [
        (errors.ForgeError, "error", 400),
        (errors.ValidationFailed, "validation_failed", 400),
        (errors.Unauthenticated, "unauthenticated", 401),
        (errors.PermissionRefused, "permission_refused", 403),
        (errors.NotFound, "not_found", 404),
        (errors.Conflict, "conflict", 409),
    ],
)
def test_defaults(cls, code, status):
    error = cls("boom")
    assert (error.code, error.status, error.detail) == (code, status, "boom")
    assert str(error) == "boom"


def test_detail_defaults_to_code():
    assert errors.NotFound().detail == "not_found"


def test_custom_code_does_not_change_the_class():
    error = errors.Conflict("x", code="email_taken")
    assert error.code == "email_taken"
    assert errors.Conflict.code == "conflict"


def test_as_dict_without_extra():
    assert errors.NotFound("gone").as_dict() == {"code": "not_found", "detail": "gone"}


def test_as_dict_with_extra():
    payload = errors.ValidationFailed("bad", extra={"field": "email"}).as_dict()
    assert payload["extra"] == {"field": "email"}


def test_all_are_exceptions_of_forge_error():
    for cls in (errors.ValidationFailed, errors.NotFound, errors.Conflict):
        assert issubclass(cls, errors.ForgeError) and issubclass(cls, Exception)
