from app.domains.geo.service import PLACES, PlaceSearchService


def test_local_place_index_covers_all_current_province_level_units() -> None:
    assert len(PLACES) == 34
    assert {item.place_id for item in PLACES} >= {
        "vn-hanoi",
        "vn-ho-chi-minh",
        "vn-hai-phong",
        "vn-hue",
        "vn-da-nang",
        "vn-can-tho",
    }


def test_place_search_is_accent_insensitive_and_never_needs_gps() -> None:
    service = PlaceSearchService()

    assert service.search("dak lak")[0].place_id == "vn-dak-lak"
    assert service.search("Điện Biên")[0].place_id == "vn-dien-bien"
    lam_dong = service.get("vn-lam-dong")
    assert lam_dong is not None
    assert lam_dong.timezone_id == "Asia/Ho_Chi_Minh"
