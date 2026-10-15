import pytest
from pycatch import Err, Ok, catch
from rest_framework.exceptions import NotAuthenticated
from rest_framework.test import APIRequestFactory

from forge_core.drf import error_response, exception_handler, respond
from forge_core.errors import Conflict, ForgeError, NotFound


def test_ok_becomes_response():
    response = respond(Ok({"id": 1}))
    assert response.status_code == 200 and response.data == {"id": 1}


def test_ok_with_custom_status():
    assert respond(Ok({}), status=201).status_code == 201


def test_forge_error_becomes_error_response():
    response = respond(Err(NotFound("gone")))
    assert response.status_code == 404
    assert response.data == {"code": "not_found", "detail": "gone"}


def test_other_exceptions_are_raised():
    with pytest.raises(ZeroDivisionError):
        respond(Err(ZeroDivisionError()))


def test_non_result_is_rejected():
    with pytest.raises(TypeError, match="Result"):
        respond({"id": 1})


def test_error_response_status_follows_error():
    assert error_response(Conflict("x")).status_code == 409


def test_catch_decorator_integration():
    @catch(ForgeError)
    def service(fail: bool):
        if fail:
            raise NotFound("missing")
        return {"ok": True}

    assert respond(service(False)).data == {"ok": True}
    assert respond(service(True)).status_code == 404


def test_exception_handler_handles_forge_error():
    response = exception_handler(NotFound("gone"), {})
    assert response.status_code == 404


def test_exception_handler_delegates_to_drf():
    request = APIRequestFactory().get("/")
    context = {"request": request, "view": None, "args": (), "kwargs": {}}
    response = exception_handler(NotAuthenticated(), context)
    assert response.status_code == 401


def test_exception_handler_ignores_unknown_exceptions():
    assert exception_handler(RuntimeError("x"), {}) is None
