from datetime import datetime

from app.domains.astro.models import (
    BodyName,
    DateOnlySunResult,
    NatalChart,
    Tradition,
    TransitToNatalSnapshot,
)
from app.domains.readings.models import (
    BackgroundLens,
    InsightReading,
    ReadingClaim,
    ReadingDomain,
    ReadingPlan,
    ReadingPurpose,
)
from app.domains.readings.planner import ReadingPlanner

SIGN_VI = {
    "aries": "Bạch Dương",
    "taurus": "Kim Ngưu",
    "gemini": "Song Tử",
    "cancer": "Cự Giải",
    "leo": "Sư Tử",
    "virgo": "Xử Nữ",
    "libra": "Thiên Bình",
    "scorpio": "Bọ Cạp",
    "sagittarius": "Nhân Mã",
    "capricorn": "Ma Kết",
    "aquarius": "Bảo Bình",
    "pisces": "Song Ngư",
}

BODY_VI = {
    BodyName.SUN: "Mặt Trời",
    BodyName.MOON: "Mặt Trăng",
    BodyName.MERCURY: "Sao Thủy",
    BodyName.VENUS: "Sao Kim",
    BodyName.MARS: "Sao Hỏa",
    BodyName.JUPITER: "Sao Mộc",
}

BODY_FUNCTION = {
    BodyName.SUN: "cách bạn chủ động, tạo dấu ấn và cảm thấy mình đang sống đúng hướng",
    BodyName.MOON: "cách bạn xử lý cảm xúc, tìm an toàn và hồi phục sau một ngày nhiều tín hiệu",
    BodyName.MERCURY: "cách bạn thu nhận thông tin, nối ý và nói điều mình nghĩ",
    BodyName.VENUS: "cách bạn nhận ra điều có giá trị và cảm thấy được trân trọng trong kết nối",
    BodyName.MARS: "cách bạn khởi động, theo đuổi điều mình muốn và đặt ranh giới",
    BodyName.JUPITER: (
        "cách bạn mở rộng góc nhìn, niềm tin và cảm giác còn nhiều khả năng phía trước"
    ),
}

SIGN_MODE = {
    "aries": "nhịp nhanh, thẳng và một điểm bắt đầu rõ ràng",
    "taurus": "sự ổn định, cảm giác thật và đủ thời gian để tin",
    "gemini": "trao đổi, tò mò và nhiều hơn một góc nhìn",
    "cancer": "sự thân thuộc, chăm sóc và một không gian đủ an toàn",
    "leo": "biểu đạt chân thành, độ ấm và cảm giác được nhìn thấy",
    "virgo": "chi tiết có ích, trật tự và một việc cụ thể để làm",
    "libra": "đối thoại, cân bằng và cách cư xử có qua có lại",
    "scorpio": "chiều sâu, sự riêng tư và niềm tin đã được kiểm chứng",
    "sagittarius": "khoảng rộng, ý nghĩa và quyền được thử một hướng mới",
    "capricorn": "cấu trúc, cam kết và tiến bộ có thể nhìn thấy",
    "aquarius": "khoảng thở, logic và cảm giác được kết nối mà vẫn là mình",
    "pisces": "trực giác, tưởng tượng và ranh giới đủ mềm để cảm nhận",
}

SIGN_EVERYDAY = {
    "aries": "phản ứng khá nhanh, rồi mới quay lại xem cảm giác hoặc quyết định ấy cần gì thêm",
    "taurus": "cần chạm vào điều cụ thể và giữ cách quen một lúc trước khi thật sự mở lòng",
    "gemini": (
        "nói, viết hoặc đặt câu hỏi để hiểu điều đang diễn ra thay vì ngồi yên với một đáp án"
    ),
    "cancer": "đọc không khí rất sớm và chỉ nói phần mềm nhất khi biết mình đang ở nơi an toàn",
    "leo": (
        "muốn thể hiện điều mình thật sự quan tâm và hụt hẫng khi tín hiệu ấy không được đón nhận"
    ),
    "virgo": "biến cảm giác mơ hồ thành danh sách, chi tiết hoặc một việc nhỏ có thể xử lý ngay",
    "libra": "nghĩ qua phản ứng của người kia và đôi lúc trì hoãn câu trả lời riêng của mình",
    "scorpio": "quan sát rất kỹ trước khi tin, nhưng một khi đã vào thì thường muốn đi đến tận lõi",
    "sagittarius": "tìm một ý nghĩa lớn hơn hoặc đổi bối cảnh để lấy lại cảm giác có đường đi",
    "capricorn": "giữ mình hoạt động ổn trước, còn phần dễ tổn thương thường được xử lý sau",
    "aquarius": (
        "lùi ra quan sát, đổi cảm giác thành câu hỏi hoặc tìm đúng người cùng tần số "
        "rồi mới nói sâu"
    ),
    "pisces": (
        "bắt tín hiệu rất nhanh, dễ hòa vào bầu không khí và cần thời gian tách đâu là "
        "phần của mình"
    ),
}

SIGN_SHADOW = {
    "aries": "đi quá nhanh nên bỏ lỡ điều mình thật sự cần",
    "taurus": "giữ một nhịp quen quá lâu dù nó đã không còn dễ chịu",
    "gemini": "phân tích thêm để tránh ở lại với một cảm giác chưa có tên",
    "cancer": "ôm phần của người khác rồi quên hỏi mình đang cần gì",
    "leo": "đồng nhất việc chưa được đáp lại với việc mình không đủ quan trọng",
    "virgo": "sửa mọi chi tiết trong khi điều cần nhất lại là được nghỉ",
    "libra": "giữ hòa khí bằng cách làm mờ câu trả lời thật của mình",
    "scorpio": "giữ kín quá lâu rồi để áp lực nói thay mình",
    "sagittarius": "đổi hướng quá sớm trước khi một chuyện kịp được xử lý",
    "capricorn": "biến sức chịu đựng thành tiêu chuẩn duy nhất của sự ổn",
    "aquarius": "đứng ngoài cảm xúc quá lâu nên bị hiểu thành lạnh hoặc không cần ai",
    "pisces": "nhận quá nhiều tín hiệu cùng lúc và khó biết giới hạn nằm ở đâu",
}

BODY_ACTION = {
    BodyName.SUN: (
        "Chọn một việc khiến bạn thấy có mặt thật sự hôm nay và dành cho nó 15 phút không đa nhiệm."
    ),
    BodyName.MOON: (
        "Viết một câu “mình đang cảm thấy…” và một câu “mình đang cần…” trước khi phản hồi."
    ),
    BodyName.MERCURY: "Viết ý chính trong một câu, rồi mới thêm phần giải thích nếu người kia cần.",
    BodyName.VENUS: (
        "Gọi tên một điều khiến bạn thấy được trân trọng và nói nó như một đề nghị, "
        "không phải bài test."
    ),
    BodyName.MARS: "Chọn một bước đủ nhỏ để bắt đầu và một giới hạn bạn sẽ không vượt qua hôm nay.",
    BodyName.JUPITER: (
        "Ghi lại một khả năng bạn muốn thử và một bằng chứng nhỏ cần có trước khi đi xa hơn."
    ),
}

HOUSE_TOPIC = {
    1: "cách bạn bước vào tình huống và để người khác cảm nhận mình",
    2: "giá trị cá nhân, tài nguyên và cảm giác đủ",
    3: "giao tiếp hằng ngày, học hỏi và môi trường gần",
    4: "đời sống riêng, gia đình và nơi bạn hạ cảnh giác",
    5: "sáng tạo, niềm vui, hẹn hò và quyền được chơi",
    6: "nhịp làm việc, thói quen và cách chăm cơ thể",
    7: "quan hệ một-một, cam kết và cách thương lượng",
    8: "tin cậy, thân mật, quyền lực và những gì được chia sẻ sâu",
    9: "niềm tin, học xa và cách bạn mở rộng thế giới",
    10: "vai trò công khai, hướng nghề nghiệp và điều bạn muốn xây",
    11: "bạn bè, cộng đồng và một tương lai có thể cùng làm",
    12: "đời sống bên trong, khoảng nghỉ và những tín hiệu chưa thành lời",
}

ASPECT_VI = {
    "conjunction": "đồng cung",
    "opposition": "đối đỉnh",
    "square": "vuông",
    "trine": "tam hợp",
    "sextile": "lục hợp",
    "quincunx": "quincunx",
}


class InsightReadingService:
    """Deterministic content projection; all astronomical facts come from the engine."""

    def __init__(self, planner: ReadingPlanner | None = None) -> None:
        self._planner = planner or ReadingPlanner()

    def plan(
        self,
        chart: NatalChart | DateOnlySunResult,
        *,
        purpose: ReadingPurpose,
        transits: TransitToNatalSnapshot | None = None,
        background_lens: BackgroundLens | None = None,
    ) -> ReadingPlan:
        return self._planner.plan(
            chart,
            purpose=purpose,
            transits=transits,
            background_lens=background_lens,
        )

    def overview(self, chart: NatalChart, *, observed_at: datetime) -> InsightReading:
        claims = list(
            self._jyotish_claims(chart)
            if chart.config.tradition is Tradition.JYOTISH
            else self._planet_claims(chart)
        )
        if chart.config.tradition is Tradition.JYOTISH and chart.nakshatras:
            moon = next(item for item in chart.nakshatras if item.body is BodyName.MOON)
            claims.insert(
                2,
                ReadingClaim(
                    id="moon-nakshatra",
                    domain=ReadingDomain.EMOTIONS,
                    title=f"Nakshatra {moon.name}",
                    summary=(
                        f"Mặt Trăng nằm trong vùng {moon.name}, phần {moon.pada} trong bốn phần."
                    ),
                    hook=f"Mặt Trăng của bạn đi qua vùng {moon.name}, pada {moon.pada}.",
                    meaning=(
                        "Trong chiêm tinh Ấn Độ, mỗi cung còn được chia thành các vùng nhỏ hơn. "
                        "Vị trí này đã tính từ ngày, giờ và nơi "
                        "sinh. Phần giải nghĩa riêng chưa sẵn sàng."
                    ),
                    manifestation=(
                        f"Mặt Trăng nằm ở phần {moon.pada} của vùng {moon.name}. "
                        "Đây là thông tin vị trí, không phải mô tả cảm xúc của bạn."
                    ),
                    watch_for=(
                        "Hai hệ chiêm tinh có thể cho vị trí khác nhau vì dùng mốc tính khác nhau."
                    ),
                    micro_action=("Xem lại giờ và nơi sinh trước khi so sánh với lá số khác."),
                    evidence=(f"Mặt Trăng ở Nakshatra {moon.name}", f"Pada {moon.pada}"),
                    factor_refs=(f"moon:nakshatra:{moon.index}:pada:{moon.pada}",),
                    confidence="high",
                ),
            )
        return InsightReading(
            tradition=chart.config.tradition,
            config_hash=chart.config_hash,
            observed_at=observed_at,
            claims=tuple(claims[:6]),
            provenance=chart.provenance,
        )

    @staticmethod
    def _jyotish_claims(chart: NatalChart) -> tuple[ReadingClaim, ...]:
        claims: list[ReadingClaim] = []
        for body, label in BODY_VI.items():
            try:
                position = chart.body(body)
            except KeyError:
                continue
            house = InsightReadingService._house_for_longitude(chart, position.longitude)
            house_text = f", nhà {house}" if house is not None else ""
            placement = f"{label} ở {SIGN_VI[position.sign.value]}{house_text}"
            claims.append(
                ReadingClaim(
                    id=f"{body.value}-sign",
                    domain=ReadingDomain.CORE,
                    title=placement,
                    summary=f"{placement}. Vị trí đã tính theo hệ chiêm tinh Ấn Độ.",
                    hook=f"{placement}.",
                    meaning=(
                        "Lá số này dùng mốc tính của chiêm tinh Ấn Độ. "
                        "Phần giải nghĩa riêng cho hệ này chưa sẵn sàng."
                    ),
                    manifestation=f"Vị trí đã tính: {placement.lower()}.",
                    watch_for=(
                        "Vị trí có thể khác lá số phương Tây vì hai hệ dùng mốc tính khác nhau."
                    ),
                    micro_action=(
                        "Xem lại giờ, nơi sinh và cách tính đã chọn trước khi so sánh lá số."
                    ),
                    evidence=(placement,),
                    factor_refs=(f"jyotish:{body.value}:sign:{position.sign.value}",),
                    confidence="high",
                )
            )
        return tuple(claims)

    def _planet_claims(self, chart: NatalChart) -> tuple[ReadingClaim, ...]:
        definitions = (
            (BodyName.SUN, ReadingDomain.CORE, "Lõi sáng"),
            (BodyName.MOON, ReadingDomain.EMOTIONS, "Nhịp cảm xúc"),
            (BodyName.MERCURY, ReadingDomain.MIND, "Mạch suy nghĩ"),
            (BodyName.VENUS, ReadingDomain.RELATING, "Cách kết nối"),
            (BodyName.MARS, ReadingDomain.DRIVE, "Động lực"),
            (BodyName.JUPITER, ReadingDomain.CORE, "Vùng nở rộng"),
        )
        claims: list[ReadingClaim] = []
        for body, domain, title in definitions:
            try:
                position = chart.body(body)
            except KeyError:
                continue
            claims.append(
                ReadingClaim(
                    id=f"{body.value}-sign",
                    domain=domain,
                    title=title,
                    summary=self._summary(chart, body, position.sign.value),
                    hook=self._hook(body, position.sign.value),
                    meaning=self._meaning(chart, body, position.longitude, position.sign.value),
                    manifestation=self._manifestation(position.sign.value),
                    watch_for=self._watch_for(chart, body, position.sign.value),
                    micro_action=BODY_ACTION[body],
                    evidence=self._evidence_labels(
                        chart, body, position.longitude, position.sign.value
                    ),
                    factor_refs=self._factor_refs(
                        chart, body, position.longitude, position.sign.value
                    ),
                    confidence="high",
                )
            )
        return tuple(claims)

    @staticmethod
    def _summary(chart: NatalChart, body: BodyName, sign: str) -> str:
        label = BODY_VI[body]
        house = InsightReadingService._house_for_longitude(chart, chart.body(body).longitude)
        house_copy = f" · Nhà {house}" if house is not None else ""
        # The sign-only phrase made two planets in one sign read word for word alike (#143 E3);
        # the body-specific line from the detail headline keeps each card distinct.
        return f"{label} ở {SIGN_VI[sign]}{house_copy}: {InsightReadingService._hook(body, sign)}"

    @staticmethod
    def _hook(body: BodyName, sign: str) -> str:
        lead = {
            BodyName.SUN: "Bạn sáng rõ hơn",
            BodyName.MOON: "Cảm xúc của bạn dễ thở hơn",
            BodyName.MERCURY: "Đầu óc bạn bắt sóng nhanh hơn",
            BodyName.VENUS: "Bạn thấy mình được trân trọng hơn",
            BodyName.MARS: "Bạn vào guồng rõ hơn",
            BodyName.JUPITER: "Thế giới của bạn mở rộng hơn",
        }[body]
        return f"{lead} khi có {SIGN_MODE[sign]}."

    @staticmethod
    def _meaning(chart: NatalChart, body: BodyName, longitude: float, sign: str) -> str:
        label = BODY_VI[body]
        text = (
            f"{label} không nói bạn là gì; nó mô tả {BODY_FUNCTION[body]}. "
            f"Ở {SIGN_VI[sign]}, phần này có thể ưu tiên {SIGN_MODE[sign]}."
        )
        house = InsightReadingService._house_for_longitude(chart, longitude)
        if house is not None:
            text += f" Nhà {house} đưa nhịp này vào {HOUSE_TOPIC[house]}."
        return text

    @staticmethod
    def _manifestation(sign: str) -> str:
        return f"Trong đời thường, bạn có thể {SIGN_EVERYDAY[sign]}."

    @staticmethod
    def _watch_for(chart: NatalChart, body: BodyName, sign: str) -> str:
        text = f"Khi căng, bạn dễ {SIGN_SHADOW[sign]}."
        related = sorted(
            (aspect for aspect in chart.aspects if body in {aspect.body_a, aspect.body_b}),
            key=lambda aspect: aspect.orb,
        )
        if related:
            aspect = related[0]
            other = aspect.body_b if aspect.body_a is body else aspect.body_a
            dynamic = (
                "tạo thêm một điểm kéo-ngược cần điều tiết"
                if aspect.kind in {"square", "opposition", "quincunx"}
                else "tạo một đường phối hợp khá tự nhiên"
            )
            text += (
                f" Góc {ASPECT_VI.get(aspect.kind, aspect.kind)} gần nhất với "
                f"{BODY_VI.get(other, other.value.title())} {dynamic}; nó không quyết định "
                "bạn phải phản ứng thế nào."
            )
        return text

    @staticmethod
    def _evidence_labels(
        chart: NatalChart, body: BodyName, longitude: float, sign: str
    ) -> tuple[str, ...]:
        labels = [f"{BODY_VI[body]} ở {SIGN_VI[sign]}"]
        house = InsightReadingService._house_for_longitude(chart, longitude)
        if house is not None:
            labels.append(f"{BODY_VI[body]} ở Nhà {house}")
        related = sorted(
            (aspect for aspect in chart.aspects if body in {aspect.body_a, aspect.body_b}),
            key=lambda aspect: aspect.orb,
        )
        for aspect in related[:2]:
            other = aspect.body_b if aspect.body_a is body else aspect.body_a
            labels.append(
                f"{BODY_VI[body]} {ASPECT_VI.get(aspect.kind, aspect.kind)} "
                f"{BODY_VI.get(other, other.value.title())} · orb {aspect.orb:.2f}°"
            )
        return tuple(labels)

    def _factor_refs(
        self,
        chart: NatalChart,
        body: BodyName,
        longitude: float,
        sign: str,
    ) -> tuple[str, ...]:
        refs = [
            f"natal:{body.value}:longitude:{longitude:.6f}",
            f"natal:{body.value}:sign:{sign}",
        ]
        house = self._house_for_longitude(chart, longitude)
        if house is not None:
            refs.append(f"natal:{body.value}:house:{house}")
        related_aspects = sorted(
            (aspect for aspect in chart.aspects if body in {aspect.body_a, aspect.body_b}),
            key=lambda aspect: aspect.orb,
        )
        for aspect in related_aspects[:2]:
            other = aspect.body_b if aspect.body_a is body else aspect.body_a
            refs.append(
                f"natal:aspect:{body.value}:{aspect.kind}:{other.value}:orb:{aspect.orb:.3f}"
            )
        return tuple(refs)

    @staticmethod
    def _house_for_longitude(chart: NatalChart, longitude: float) -> int | None:
        if not chart.houses:
            return None
        cusps = sorted(chart.houses, key=lambda house: house.number)
        normalized = longitude % 360
        for index, house in enumerate(cusps):
            start = house.longitude % 360
            end = cusps[(index + 1) % len(cusps)].longitude % 360
            if start <= end and start <= normalized < end:
                return house.number
            if start > end and (normalized >= start or normalized < end):
                return house.number
        return None
