from dataclasses import dataclass
from unicodedata import category, normalize

from app.domains.geo.models import PlaceResult

# Resolution 202/2025/QH15 established 34 province-level units. The official
# administrative codes below follow Decision 19/2025/QD-TTg, in force for
# nationwide use from 2025-07-01. Keep persisted place IDs stable even when a
# government code or display label changes.
CURRENT_ADMIN_CODES: dict[str, str] = {
    "vn-hanoi": "01",
    "vn-cao-bang": "04",
    "vn-tuyen-quang": "08",
    "vn-dien-bien": "11",
    "vn-lai-chau": "12",
    "vn-son-la": "14",
    "vn-lao-cai": "15",
    "vn-thai-nguyen": "19",
    "vn-lang-son": "20",
    "vn-quang-ninh": "22",
    "vn-bac-ninh": "24",
    "vn-phu-tho": "25",
    "vn-hai-phong": "31",
    "vn-hung-yen": "33",
    "vn-ninh-binh": "37",
    "vn-thanh-hoa": "38",
    "vn-nghe-an": "40",
    "vn-ha-tinh": "42",
    "vn-quang-tri": "44",
    "vn-hue": "46",
    "vn-da-nang": "48",
    "vn-quang-ngai": "51",
    "vn-gia-lai": "52",
    "vn-khanh-hoa": "56",
    "vn-dak-lak": "66",
    "vn-lam-dong": "68",
    "vn-dong-nai": "75",
    "vn-ho-chi-minh": "79",
    "vn-tay-ninh": "80",
    "vn-dong-thap": "82",
    "vn-vinh-long": "86",
    "vn-an-giang": "91",
    "vn-can-tho": "92",
    "vn-ca-mau": "96",
}

PLACES: tuple[PlaceResult, ...] = (
    PlaceResult("vn-hanoi", "Hà Nội, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.0285, 105.8542),
    PlaceResult("vn-cao-bang", "Cao Bằng, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 22.6666, 106.2640),
    PlaceResult(
        "vn-tuyen-quang", "Tuyên Quang, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.8236, 105.2142
    ),
    PlaceResult("vn-dien-bien", "Điện Biên, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.3860, 103.0230),
    PlaceResult("vn-lai-chau", "Lai Châu, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 22.3862, 103.4703),
    PlaceResult("vn-son-la", "Sơn La, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.3256, 103.9188),
    PlaceResult("vn-lao-cai", "Lào Cai, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 22.4856, 103.9707),
    PlaceResult(
        "vn-thai-nguyen", "Thái Nguyên, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.5942, 105.8482
    ),
    PlaceResult("vn-lang-son", "Lạng Sơn, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.8537, 106.7610),
    PlaceResult(
        "vn-quang-ninh", "Quảng Ninh, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 20.9712, 107.0448
    ),
    PlaceResult("vn-bac-ninh", "Bắc Ninh, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.1861, 106.0763),
    PlaceResult("vn-phu-tho", "Phú Thọ, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.3987, 105.2227),
    PlaceResult("vn-hai-phong", "Hải Phòng, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 20.8449, 106.6881),
    PlaceResult("vn-hung-yen", "Hưng Yên, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 20.6464, 106.0511),
    PlaceResult("vn-ninh-binh", "Ninh Bình, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 20.2506, 105.9745),
    PlaceResult("vn-thanh-hoa", "Thanh Hóa, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 19.8067, 105.7852),
    PlaceResult("vn-nghe-an", "Nghệ An, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 18.6796, 105.6813),
    PlaceResult("vn-ha-tinh", "Hà Tĩnh, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 18.3559, 105.8877),
    PlaceResult("vn-quang-tri", "Quảng Trị, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 16.7943, 106.9634),
    PlaceResult("vn-hue", "Huế, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 16.4637, 107.5909),
    PlaceResult("vn-da-nang", "Đà Nẵng, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 16.0544, 108.2022),
    PlaceResult(
        "vn-quang-ngai", "Quảng Ngãi, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 15.1205, 108.7923
    ),
    PlaceResult("vn-gia-lai", "Gia Lai, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 13.9830, 108.0005),
    PlaceResult("vn-khanh-hoa", "Khánh Hòa, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 12.2388, 109.1967),
    PlaceResult("vn-dak-lak", "Đắk Lắk, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 12.6667, 108.0500),
    PlaceResult("vn-lam-dong", "Lâm Đồng, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 11.9404, 108.4583),
    PlaceResult("vn-dong-nai", "Đồng Nai, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.9447, 106.8243),
    PlaceResult(
        "vn-ho-chi-minh",
        "Thành phố Hồ Chí Minh, Việt Nam",
        "VN",
        "Asia/Ho_Chi_Minh",
        10.8231,
        106.6297,
    ),
    PlaceResult("vn-tay-ninh", "Tây Ninh, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 11.3352, 106.1099),
    PlaceResult("vn-dong-thap", "Đồng Tháp, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.4938, 105.6882),
    PlaceResult("vn-vinh-long", "Vĩnh Long, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.2396, 105.9572),
    PlaceResult("vn-an-giang", "An Giang, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.3759, 105.4185),
    PlaceResult("vn-can-tho", "Cần Thơ, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.0452, 105.7469),
    PlaceResult("vn-ca-mau", "Cà Mau, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 9.1769, 105.1524),
)


def _legacy(
    slug: str,
    former_name: str,
    current_name: str,
    latitude: float,
    longitude: float,
) -> PlaceResult:
    return PlaceResult(
        f"vn-former-{slug}",
        f"{former_name} (tên trước 2025 · nay thuộc {current_name}), Việt Nam",
        "VN",
        "Asia/Ho_Chi_Minh",
        latitude,
        longitude,
        confidence="former-province-centroid",
    )


# Birthplaces do not move when administrative boundaries change. These legacy
# entries let people find all 29 former province names while preserving a local
# representative coordinate instead of silently replacing it with the centroid
# of a much larger merged province.
FORMER_PLACES: tuple[PlaceResult, ...] = (
    _legacy("ha-giang", "Hà Giang", "Tuyên Quang", 22.8233, 104.9836),
    _legacy("yen-bai", "Yên Bái", "Lào Cai", 21.7168, 104.8986),
    _legacy("bac-kan", "Bắc Kạn", "Thái Nguyên", 22.1470, 105.8348),
    _legacy("vinh-phuc", "Vĩnh Phúc", "Phú Thọ", 21.3089, 105.6049),
    _legacy("hoa-binh", "Hòa Bình", "Phú Thọ", 20.8172, 105.3376),
    _legacy("bac-giang", "Bắc Giang", "Bắc Ninh", 21.2810, 106.1975),
    _legacy("thai-binh", "Thái Bình", "Hưng Yên", 20.4463, 106.3366),
    _legacy("hai-duong", "Hải Dương", "Hải Phòng", 20.9373, 106.3146),
    _legacy("ha-nam", "Hà Nam", "Ninh Bình", 20.5835, 105.9229),
    _legacy("nam-dinh", "Nam Định", "Ninh Bình", 20.4388, 106.1621),
    _legacy("quang-binh", "Quảng Bình", "Quảng Trị", 17.4689, 106.6223),
    _legacy("quang-nam", "Quảng Nam", "Đà Nẵng", 15.5736, 108.4740),
    _legacy("kon-tum", "Kon Tum", "Quảng Ngãi", 14.3497, 108.0005),
    _legacy("binh-dinh", "Bình Định", "Gia Lai", 13.7820, 109.2190),
    _legacy("ninh-thuan", "Ninh Thuận", "Khánh Hòa", 11.5826, 108.9912),
    _legacy("dak-nong", "Đắk Nông", "Lâm Đồng", 12.0045, 107.6907),
    _legacy("binh-thuan", "Bình Thuận", "Lâm Đồng", 10.9804, 108.2615),
    _legacy("phu-yen", "Phú Yên", "Đắk Lắk", 13.0955, 109.3209),
    _legacy("binh-duong", "Bình Dương", "TP Hồ Chí Minh", 10.9804, 106.6519),
    _legacy("ba-ria-vung-tau", "Bà Rịa - Vũng Tàu", "TP Hồ Chí Minh", 10.4114, 107.1362),
    _legacy("binh-phuoc", "Bình Phước", "Đồng Nai", 11.5344, 106.8832),
    _legacy("long-an", "Long An", "Tây Ninh", 10.5359, 106.4137),
    _legacy("hau-giang", "Hậu Giang", "Cần Thơ", 9.7845, 105.4701),
    _legacy("soc-trang", "Sóc Trăng", "Cần Thơ", 9.6025, 105.9739),
    _legacy("ben-tre", "Bến Tre", "Vĩnh Long", 10.2434, 106.3756),
    _legacy("tra-vinh", "Trà Vinh", "Vĩnh Long", 9.9347, 106.3453),
    _legacy("tien-giang", "Tiền Giang", "Đồng Tháp", 10.3600, 106.3600),
    _legacy("bac-lieu", "Bạc Liêu", "Cà Mau", 9.2940, 105.7278),
    _legacy("kien-giang", "Kiên Giang", "An Giang", 10.0125, 105.0809),
)

CURRENT_SEARCH_ALIASES: dict[str, tuple[str, ...]] = {
    "vn-hanoi": ("ha noi",),
    "vn-ho-chi-minh": ("tp hcm", "tphcm", "ho chi minh", "sai gon", "saigon"),
    "vn-hai-phong": ("hai phong",),
    "vn-hue": ("thua thien hue",),
    "vn-da-nang": ("da nang",),
    "vn-can-tho": ("can tho",),
    "vn-dak-lak": ("dak lak", "dac lac"),
}


def _normalize(value: str) -> str:
    decomposed = normalize("NFD", value.strip().casefold())
    return "".join(char for char in decomposed if category(char) != "Mn").replace("đ", "d")


@dataclass(frozen=True, slots=True)
class _IndexedPlace:
    place: PlaceResult
    search_text: str


def _search_text(place: PlaceResult, extra: tuple[str, ...] = ()) -> str:
    return " ".join((_normalize(place.display_name), *(_normalize(item) for item in extra)))


SEARCH_INDEX: tuple[_IndexedPlace, ...] = tuple(
    _IndexedPlace(place, _search_text(place, CURRENT_SEARCH_ALIASES.get(place.place_id, ())))
    for place in PLACES
) + tuple(
    # Only index the former name. Searching a new province must not return all
    # of its legacy components and bury the canonical current result.
    _IndexedPlace(place, _normalize(place.display_name.split(" (", maxsplit=1)[0]))
    for place in FORMER_PLACES
)

PLACE_BY_ID = {place.place_id: place for place in (*PLACES, *FORMER_PLACES)}


class PlaceSearchService:
    def search(self, query: str) -> tuple[PlaceResult, ...]:
        normalized = _normalize(query)
        if not normalized:
            return PLACES
        if len(normalized) < 2:
            return ()
        return tuple(item.place for item in SEARCH_INDEX if normalized in item.search_text)[:8]

    def get(self, place_id: str) -> PlaceResult | None:
        return PLACE_BY_ID.get(place_id)
