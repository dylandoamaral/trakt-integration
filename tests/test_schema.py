from custom_components.trakt_tv.schema import configuration_schema, dictionary_to_schema


class TestSchema:
    def test_dictionary_to_schema(self):
        schema = dictionary_to_schema({"name": str})
        schema({"name": "john"})

    def test_configuration_schema(self, configuration):
        configuration_schema(configuration.conf)
