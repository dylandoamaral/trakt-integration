from custom_components.trakt_tv.configuration import Configuration


class TestConfiguration:
    def test_conf(self, configuration):
        assert configuration.conf["language"] == "fr"

    def test_upcoming_identifier_exists(self, configuration):
        assert configuration.upcoming_identifier_exists("movie") is True

    def test_identifier_not_exists(self, configuration):
        assert configuration.upcoming_identifier_exists("show") is False

    def test_get_upcoming_days_to_fetch(self, configuration):
        assert configuration.get_upcoming_days_to_fetch("movie") == 60

    def test_get_upcoming_days_to_fetch_default(self, configuration):
        assert configuration.get_upcoming_days_to_fetch("show") == 30

    def test_get_language(self, configuration):
        assert configuration.get_language() == "fr"

    def test_get_language_default(self):
        configuration = Configuration(data={})
        assert configuration.get_language() == "en"
