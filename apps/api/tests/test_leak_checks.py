from tests.leak_checks import leaked


def test_a_timestamp_written_at_the_birth_minute_is_not_a_leak() -> None:
    # The CI run of 14.11.2026 19:03 UTC: created_at carried "19:00" and the check failed.
    payload = str(
        {"created_at": "2026-11-14T19:00:41.512Z", "updated_at": "2026-11-14 19:00:41+00:00"}
    )
    assert leaked(payload, ("19:00", "08:15")) == []


def test_a_birth_time_on_its_own_is_still_a_leak() -> None:
    assert leaked(str({"time": "19:00"}), ("19:00",)) == ["19:00"]
    assert leaked("sinh lúc 19:00 tối", ("19:00",)) == ["19:00"]
    assert leaked(str({"at": "1990-01-01T19:00"}), ("1990-01-01", "19:00")) == ["1990-01-01"]


def test_other_values_are_checked_in_the_payload_as_it_is() -> None:
    assert leaked("2026-11-14T19:00Z birth_time", ("birth_time", "10.8231")) == ["birth_time"]
