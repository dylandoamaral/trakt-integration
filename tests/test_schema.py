import pytest
from voluptuous import MultipleInvalid

from custom_components.trakt_tv.schema import (
    collection_schema,
    configuration_schema,
    dictionary_to_schema,
)


class TestSchema:
    def test_dictionary_to_schema(self):
        schema = dictionary_to_schema({"name": str})
        schema({"name": "john"})

    def test_configuration_schema(self, configuration):
        configuration_schema(configuration.conf)

    def test_collection_schema_defaults(self):
        configuration = dictionary_to_schema(collection_schema())({"movie": {}})

        assert configuration["movie"]["max_medias"] == 20

    @pytest.mark.parametrize(
        "option",
        ["sort_by", "sort_order", "only_released", "only_unwatched"],
    )
    def test_collection_schema_rejects_watchlist_options(self, option):
        schema = dictionary_to_schema(collection_schema())

        with pytest.raises(MultipleInvalid):
            schema({"movie": {option: True}})
