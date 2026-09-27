from app.domains.geo.service import CURRENT_ADMIN_CODES, FORMER_PLACES, PLACES, PlaceSearchService


def test_local_place_index_covers_all_current_province_level_units() -> None:
    assert len(PLACES) == 34
    assert len(CURRENT_ADMIN_CODES) == 34
    assert {item.place_id for item in PLACES} == set(CURRENT_ADMIN_CODES)
    assert set(CURRENT_ADMIN_CODES.values()) == {
        "01",
        "04",
        "08",
        "11",
        "12",
        "14",
        "15",
        "19",
        "20",
        "22",
        "24",
        "25",
        "31",
        "33",
        "37",
        "38",
        "40",
        "42",
        "44",
        "46",
        "48",
        "51",
        "52",
        "56",
        "66",
        "68",
        "75",
        "79",
        "80",
        "82",
        "86",
        "91",
        "92",
        "96",
    }


def test_empty_search_lists_all_current_units_and_not_historical_aliases() -> None:
    results = PlaceSearchService().search("")

    assert results == PLACES
    assert len(FORMER_PLACES) == 29
    assert all("tên trước 2025" not in item.display_name for item in results)


def test_place_search_is_accent_insensitive_and_never_needs_gps() -> None:
    service = PlaceSearchService()

    assert service.search("dak lak")[0].place_id == "vn-dak-lak"
    assert service.search("Điện Biên")[0].place_id == "vn-dien-bien"
    lam_dong = service.get("vn-lam-dong")
    assert lam_dong is not None
    assert lam_dong.timezone_id == "Asia/Ho_Chi_Minh"


def test_former_province_names_resolve_without_hiding_the_current_mapping() -> None:
    service = PlaceSearchService()

    binh_duong = service.search("Bình Dương")
    quang_nam = service.search("quang nam")

    assert binh_duong[0].place_id == "vn-former-binh-duong"
    assert "nay thuộc TP Hồ Chí Minh" in binh_duong[0].display_name
    assert binh_duong[0].confidence == "former-province-centroid"
    assert quang_nam[0].place_id == "vn-former-quang-nam"
    assert "nay thuộc Đà Nẵng" in quang_nam[0].display_name
    assert service.get("vn-former-quang-nam") == quang_nam[0]


def test_searching_current_name_does_not_bury_it_under_legacy_results() -> None:
    service = PlaceSearchService()

    assert service.search("TP HCM")[0].place_id == "vn-ho-chi-minh"
    assert service.search("Sài Gòn")[0].place_id == "vn-ho-chi-minh"
    assert service.search("Đà Nẵng")[0].place_id == "vn-da-nang"
