from unicodedata import category, normalize

from app.domains.geo.models import PlaceResult

PLACES: tuple[PlaceResult, ...] = (
    PlaceResult("vn-hanoi", "Hà Nội, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.0285, 105.8542),
    PlaceResult(
        "vn-ho-chi-minh",
        "Thành phố Hồ Chí Minh, Việt Nam",
        "VN",
        "Asia/Ho_Chi_Minh",
        10.8231,
        106.6297,
    ),
    PlaceResult("vn-da-nang", "Đà Nẵng, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 16.0544, 108.2022),
    PlaceResult("vn-hue", "Huế, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 16.4637, 107.5909),
    PlaceResult("vn-can-tho", "Cần Thơ, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.0452, 105.7469),
    PlaceResult("vn-hai-phong", "Hải Phòng, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 20.8449, 106.6881),
    PlaceResult("vn-bac-ninh", "Bắc Ninh, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.1861, 106.0763),
    PlaceResult(
        "vn-quang-ninh", "Quảng Ninh, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 20.9712, 107.0448
    ),
    PlaceResult("vn-ninh-binh", "Ninh Bình, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 20.2506, 105.9745),
    PlaceResult("vn-hung-yen", "Hưng Yên, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 20.6464, 106.0511),
    PlaceResult("vn-phu-tho", "Phú Thọ, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.3987, 105.2227),
    PlaceResult(
        "vn-thai-nguyen", "Thái Nguyên, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.5942, 105.8482
    ),
    PlaceResult(
        "vn-tuyen-quang", "Tuyên Quang, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.8236, 105.2142
    ),
    PlaceResult("vn-lao-cai", "Lào Cai, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 22.4856, 103.9707),
    PlaceResult("vn-cao-bang", "Cao Bằng, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 22.6666, 106.2640),
    PlaceResult("vn-lang-son", "Lạng Sơn, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.8537, 106.7610),
    PlaceResult("vn-lai-chau", "Lai Châu, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 22.3862, 103.4703),
    PlaceResult("vn-dien-bien", "Điện Biên, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.3860, 103.0230),
    PlaceResult("vn-son-la", "Sơn La, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 21.3256, 103.9188),
    PlaceResult("vn-thanh-hoa", "Thanh Hóa, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 19.8067, 105.7852),
    PlaceResult("vn-nghe-an", "Nghệ An, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 18.6796, 105.6813),
    PlaceResult("vn-ha-tinh", "Hà Tĩnh, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 18.3559, 105.8877),
    PlaceResult("vn-quang-tri", "Quảng Trị, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 16.7943, 106.9634),
    PlaceResult(
        "vn-quang-ngai", "Quảng Ngãi, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 15.1205, 108.7923
    ),
    PlaceResult("vn-gia-lai", "Gia Lai, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 13.9830, 108.0005),
    PlaceResult("vn-khanh-hoa", "Khánh Hòa, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 12.2388, 109.1967),
    PlaceResult("vn-dak-lak", "Đắk Lắk, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 12.6667, 108.0500),
    PlaceResult("vn-lam-dong", "Lâm Đồng, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 11.9404, 108.4583),
    PlaceResult("vn-dong-nai", "Đồng Nai, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.9447, 106.8243),
    PlaceResult("vn-tay-ninh", "Tây Ninh, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 11.3352, 106.1099),
    PlaceResult("vn-vinh-long", "Vĩnh Long, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.2396, 105.9572),
    PlaceResult("vn-dong-thap", "Đồng Tháp, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.4938, 105.6882),
    PlaceResult("vn-ca-mau", "Cà Mau, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 9.1769, 105.1524),
    PlaceResult("vn-an-giang", "An Giang, Việt Nam", "VN", "Asia/Ho_Chi_Minh", 10.3759, 105.4185),
)


class PlaceSearchService:
    def search(self, query: str) -> tuple[PlaceResult, ...]:
        normalized = _normalize(query)
        if len(normalized) < 2:
            return ()
        return tuple(place for place in PLACES if normalized in _normalize(place.display_name))[:8]

    def get(self, place_id: str) -> PlaceResult | None:
        return next((place for place in PLACES if place.place_id == place_id), None)


def _normalize(value: str) -> str:
    decomposed = normalize("NFD", value.strip().casefold())
    return "".join(char for char in decomposed if category(char) != "Mn").replace("đ", "d")
