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

    def test_watchlist_identifier_exists(self, configuration):
        assert configuration.watchlist_identifier_exists("movie") is True
        assert configuration.watchlist_identifier_exists("show") is False

    def test_get_watchlist_max_medias_default(self, configuration):
        assert configuration.get_watchlist_max_medias("movie") == 20

    def test_get_watchlist_sort_by(self, configuration):
        assert configuration.get_watchlist_sort_by("movie") == "rating"

    def test_get_watchlist_sort_order(self, configuration):
        assert configuration.get_watchlist_sort_order("movie") == "desc"

    def test_is_watchlist_only_released_default(self, configuration):
        assert configuration.is_watchlist_only_released("movie") is True

    def test_is_watchlist_only_unwatched_default(self, configuration):
        assert configuration.is_watchlist_only_unwatched("movie") is True
