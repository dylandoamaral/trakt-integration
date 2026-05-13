from custom_components.trakt_tv.configuration import Configuration
from custom_components.trakt_tv.const import DOMAIN
from custom_components.trakt_tv.defaults import merge_sensor_config


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

    def test_get_timezone_falls_back_to_utc_for_abbreviation(self):
        configuration = Configuration(
            data={DOMAIN: {"configuration": {"timezone": "IST"}}}
        )
        assert configuration.get_timezone() == "UTC"

    def test_get_timezone_accepts_iana_zone(self):
        configuration = Configuration(
            data={DOMAIN: {"configuration": {"timezone": "Europe/Dublin"}}}
        )
        assert configuration.get_timezone() == "Europe/Dublin"

    def test_get_timezone_missing_defaults_to_utc(self):
        configuration = Configuration(data={DOMAIN: {"configuration": {}}})
        assert configuration.get_timezone() == "UTC"

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


def _build_data(options=None, yaml_sensors=None):
    sensors = merge_sensor_config(yaml_sensors, options)
    return {DOMAIN: {"configuration": {"sensors": sensors, "language": "en"}}}


class TestUiManagedConfiguration:
    def test_defaults_enable_all_groups(self):
        configuration = Configuration(data=_build_data())
        assert configuration.upcoming_identifier_exists("movie") is True
        assert (
            configuration.upcoming_identifier_exists("movie", all_medias=True) is True
        )
        assert configuration.recommendation_identifier_exists("movie") is True
        assert configuration.anticipated_identifier_exists("movie") is True
        assert configuration.next_to_watch_identifier_exists("all") is True
        assert configuration.watchlist_identifier_exists("movie") is True
        assert configuration.watchlist_identifier_exists("show") is True
        assert configuration.source_exists("stats") is True
        assert configuration.source_exists("now_playing") is True

    def test_disable_watchlist_removes_group(self):
        configuration = Configuration(
            data=_build_data(options={"enable_watchlist": False})
        )
        assert configuration.watchlist_identifier_exists("movie") is False
        assert configuration.watchlist_identifier_exists("show") is False

    def test_disable_now_playing_removes_source(self):
        configuration = Configuration(
            data=_build_data(options={"enable_now_playing": False})
        )
        assert configuration.source_exists("now_playing") is False

    def test_disable_upcoming_removes_identifiers(self):
        configuration = Configuration(
            data=_build_data(options={"enable_upcoming": False})
        )
        assert configuration.upcoming_identifier_exists("movie") is False
        # all_upcoming is unaffected
        assert (
            configuration.upcoming_identifier_exists("movie", all_medias=True) is True
        )

    def test_yaml_sensors_survive_when_no_options(self):
        configuration = Configuration(
            data=_build_data(
                yaml_sensors={
                    "upcoming": {"movie": {"days_to_fetch": 60, "max_medias": 5}}
                }
            )
        )
        # YAML value wins for upcoming.movie
        assert configuration.get_upcoming_days_to_fetch("movie") == 60
        # Other groups still get defaults
        assert configuration.watchlist_identifier_exists("movie") is True
