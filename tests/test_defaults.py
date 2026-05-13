from custom_components.trakt_tv.defaults import (
    SENSOR_GROUPS,
    apply_options_to_sensors,
    build_default_sensors_config,
    default_sensor_config_for_group,
    merge_sensor_config,
    options_enabled_groups,
)


class TestDefaults:
    def test_default_sensors_includes_all_groups(self):
        sensors = build_default_sensors_config()
        for group in SENSOR_GROUPS:
            assert group in sensors, f"missing default for {group}"

    def test_upcoming_defaults_have_required_keys(self):
        sensors = build_default_sensors_config()
        for identifier, value in sensors["upcoming"].items():
            assert value["max_medias"] == 3
            assert value["days_to_fetch"] == 30

    def test_next_to_watch_defaults_have_sort_options(self):
        sensors = build_default_sensors_config()
        for value in sensors["next_to_watch"].values():
            assert value["sort_by"] == "released"
            assert value["sort_order"] == "asc"
            assert value["exclude"] == []
            assert value["max_medias"] == 3

    def test_watchlist_defaults_for_both_kinds(self):
        sensors = build_default_sensors_config()
        for identifier in ("movie", "show"):
            assert sensors["watchlist"][identifier]["only_released"] is True
            assert sensors["watchlist"][identifier]["only_unwatched"] is True
            assert sensors["watchlist"][identifier]["max_medias"] == 20

    def test_now_playing_default_enabled(self):
        sensors = build_default_sensors_config()
        assert sensors["now_playing"] == {"enabled": True}

    def test_stats_defaults_to_all(self):
        sensors = build_default_sensors_config()
        assert sensors["stats"] == ["all"]

    def test_default_sensor_config_for_unknown_group(self):
        assert default_sensor_config_for_group("nope") is None


class TestOptions:
    def test_options_enabled_groups_defaults_to_true(self):
        enabled = options_enabled_groups(None)
        for group in SENSOR_GROUPS:
            assert enabled[group] is True

    def test_options_disable_specific_groups(self):
        enabled = options_enabled_groups(
            {"enable_watchlist": False, "enable_now_playing": False}
        )
        assert enabled["watchlist"] is False
        assert enabled["now_playing"] is False
        assert enabled["upcoming"] is True

    def test_apply_options_removes_disabled_groups(self):
        sensors = build_default_sensors_config()
        filtered = apply_options_to_sensors(
            sensors,
            {"enable_watchlist": False, "enable_stats": False},
        )
        assert "watchlist" not in filtered
        assert "stats" not in filtered
        assert "upcoming" in filtered
        assert "now_playing" in filtered


class TestMerge:
    def test_merge_without_yaml_yields_full_defaults(self):
        sensors = merge_sensor_config(None, None)
        for group in SENSOR_GROUPS:
            assert group in sensors

    def test_merge_disables_via_options(self):
        sensors = merge_sensor_config(
            None,
            {"enable_anticipated": False, "enable_recommendation": False},
        )
        assert "anticipated" not in sensors
        assert "recommendation" not in sensors

    def test_merge_preserves_yaml_overrides(self):
        yaml_sensors = {
            "upcoming": {"movie": {"days_to_fetch": 60, "max_medias": 5}},
        }
        sensors = merge_sensor_config(yaml_sensors, None)
        assert sensors["upcoming"] == yaml_sensors["upcoming"]
        assert "watchlist" in sensors

    def test_merge_keeps_lists_yaml(self):
        yaml_sensors = {
            "lists": [
                {
                    "list_id": "watchlist",
                    "friendly_name": "Mine",
                    "max_medias": 3,
                    "private_list": True,
                    "media_type": "",
                    "sort_by": "rank",
                    "sort_order": "asc",
                }
            ],
        }
        sensors = merge_sensor_config(yaml_sensors, None)
        assert sensors["lists"] == yaml_sensors["lists"]

    def test_merge_yaml_user_can_disable_via_options(self):
        yaml_sensors = {
            "watchlist": {"movie": {"max_medias": 10}},
        }
        sensors = merge_sensor_config(yaml_sensors, {"enable_watchlist": False})
        assert "watchlist" not in sensors
