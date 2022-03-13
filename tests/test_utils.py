from freezegun import freeze_time

from custom_components.trakt_tv.utils import compute_calendar_args, split


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
            ("2022-03-13", 33),
            ("2022-04-15", 33),
            ("2022-05-18", 24),
        ]
