from dataclasses import dataclass
from typing import Any, Dict

from custom_components.trakt_tv.const import DOMAIN


@dataclass
class Configuration:
    data: Dict[str, Any]

    @property
    def conf(self) -> Dict[str, Any]:
        return self.data[DOMAIN]["configuration"]

    def identifier_exists(self, identifier: str) -> bool:
        try:
            self.conf["sensors"]["upcoming"][identifier]
            return True
        except KeyError:
            return False

    def get_days_to_fetch(self, identifier: str) -> int:
        try:
            return self.conf["sensors"]["upcoming"][identifier]["days_to_fetch"]
        except KeyError:
            return 30

    def get_language(self) -> int:
        try:
            return self.conf["language"]
        except KeyError:
            return "en"
