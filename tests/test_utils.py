import pytest
from freezegun import freeze_time

from custom_components.trakt_tv.exception import TraktException
from custom_components.trakt_tv.utils import (
    cache_insert,
    cache_retrieve,
    compute_calendar_args,
    deserialize_json,
    split,
)


class TestUtils:
    def test_split(self):
        assert split(10, 3) == [3, 3, 3, 1]
        assert split(1, 3) == [1]
        assert split(3, 3) == [3]
        assert split(9, 3) == [3, 3, 3]

    def test_split_trakt(self):
        assert split(90, 33) == [33, 33, 24]

    @freeze_time("2022-03-13")
    def test_compute_calendar_args(self):
        assert compute_calendar_args(90, 33) == [
            ("2022-03-12", 33),
            ("2022-04-14", 33),
            ("2022-05-17", 24),
        ]

    def test_deserialize_json_success(self):
        json = '{"name":"Trakt"}'
        dictionary = deserialize_json(json)
        assert dictionary["name"] == "Trakt"

    def test_deserialize_json_error(self):
        json = '{"name":"}'
        with pytest.raises(TraktException):
            deserialize_json(json)

    @freeze_time("2022-03-13")
    def test_cache_insert(self):
        cache = {}
        expected = {"key": 10, "key_time": 1647129600.0}

        cache_insert(cache, "key", 10)

        assert cache == expected

    @freeze_time("2022-03-13")
    def test_cache_retrieve_exists(self):
        cache = {"key": 10, "key_time": 1647129600.0}

        value = cache_retrieve(cache, "key")

        assert value == 10

    @freeze_time("2022-03-14")
    def test_cache_retrieve_expired(self):
        cache = {"key": 10, "key_time": 1647129600.0}

        value = cache_retrieve(cache, "key")

        assert value == None
        assert cache == {}

    def test_cache_retrieve_missing(self):
        cache = {}

        value = cache_retrieve(cache, "key")

        assert value == None
