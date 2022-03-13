from pytest import fixture

from custom_components.trakt_tv.configuration import Configuration
from custom_components.trakt_tv.const import DOMAIN


@fixture
def yaml():
    return {
        DOMAIN: {
            "configuration": {
                "language": "fr",
                "sensors": {"upcoming": {"movie": {"days_to_fetch": 60}}},
            }
        }
    }


@fixture
def configuration(yaml):
    return Configuration(data=yaml)
