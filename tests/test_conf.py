import pytest
from django.core.exceptions import ImproperlyConfigured

from forge_core.conf import (
    current_environment,
    deep_merge,
    env,
    env_bool,
    env_float,
    env_int,
    env_list,
)


class TestEnv:
    def test_reads_string(self, monkeypatch):
        monkeypatch.setenv("X", "value")
        assert env("X") == "value"

    def test_missing_without_default_names_the_variable(self, monkeypatch):
        monkeypatch.delenv("X", raising=False)
        with pytest.raises(ImproperlyConfigured, match="X"):
            env("X")

    def test_default_is_returned_untouched(self, monkeypatch):
        monkeypatch.delenv("X", raising=False)
        assert env("X", default=None) is None
        assert env("X", default=3, cast=str) == 3

    def test_empty_value_is_not_missing(self, monkeypatch):
        monkeypatch.setenv("X", "")
        assert env("X", default="d") == ""

    def test_cast_failure_is_reported(self, monkeypatch):
        monkeypatch.setenv("X", "abc")
        with pytest.raises(ImproperlyConfigured, match="X"):
            env("X", cast=int)


class TestTypedReaders:
    @pytest.mark.parametrize("raw", ["1", "true", "True", "YES", "on", "oui", " true "])
    def test_bool_true(self, monkeypatch, raw):
        monkeypatch.setenv("B", raw)
        assert env_bool("B") is True

    @pytest.mark.parametrize("raw", ["0", "false", "False", "NO", "off", "non", ""])
    def test_bool_false(self, monkeypatch, raw):
        monkeypatch.setenv("B", raw)
        assert env_bool("B") is False

    def test_bool_invalid(self, monkeypatch):
        monkeypatch.setenv("B", "maybe")
        with pytest.raises(ImproperlyConfigured):
            env_bool("B")

    def test_bool_default(self, monkeypatch):
        monkeypatch.delenv("B", raising=False)
        assert env_bool("B", default=True) is True

    def test_int(self, monkeypatch):
        monkeypatch.setenv("N", "42")
        assert env_int("N") == 42

    def test_int_invalid(self, monkeypatch):
        monkeypatch.setenv("N", "4.2")
        with pytest.raises(ImproperlyConfigured):
            env_int("N")

    def test_float(self, monkeypatch):
        monkeypatch.setenv("F", "1.5")
        assert env_float("F") == 1.5

    def test_list_trims_and_drops_empty_items(self, monkeypatch):
        monkeypatch.setenv("L", " a, b ,,c ")
        assert env_list("L") == ["a", "b", "c"]

    def test_list_custom_separator(self, monkeypatch):
        monkeypatch.setenv("L", "a;b")
        assert env_list("L", sep=";") == ["a", "b"]

    def test_list_empty_value(self, monkeypatch):
        monkeypatch.setenv("L", "")
        assert env_list("L") == []

    def test_list_default(self, monkeypatch):
        monkeypatch.delenv("L", raising=False)
        assert env_list("L", default=["localhost"]) == ["localhost"]


class TestEnvironmentName:
    def test_default_is_dev(self, monkeypatch):
        monkeypatch.delenv("FORGE_ENV", raising=False)
        assert current_environment() == "dev"

    def test_is_normalised(self, monkeypatch):
        monkeypatch.setenv("FORGE_ENV", " Prod ")
        assert current_environment() == "prod"


class TestDeepMerge:
    def test_last_layer_wins(self):
        assert deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_nested_dicts_are_merged(self):
        base = {"LOGGING": {"version": 1, "root": {"level": "INFO"}}}
        prod = {"LOGGING": {"root": {"level": "WARNING"}, "disable_existing_loggers": False}}
        assert deep_merge(base, prod) == {
            "LOGGING": {
                "version": 1,
                "root": {"level": "WARNING"},
                "disable_existing_loggers": False,
            }
        }

    def test_lists_are_replaced_not_concatenated(self):
        assert deep_merge({"h": ["a"]}, {"h": ["b"]}) == {"h": ["b"]}

    def test_inputs_are_not_mutated(self):
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        result = deep_merge(base, override)
        result["a"]["b"] = 99
        assert base == {"a": {"b": 1}} and override == {"a": {"c": 2}}

    def test_mapping_replaces_scalar_and_back(self):
        assert deep_merge({"a": 1}, {"a": {"b": 2}}) == {"a": {"b": 2}}
        assert deep_merge({"a": {"b": 2}}, {"a": 1}) == {"a": 1}

    def test_no_layers(self):
        assert deep_merge() == {}
