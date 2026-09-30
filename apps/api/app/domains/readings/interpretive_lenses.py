from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from hashlib import sha256

from app.domains.readings.models import BackgroundLens

METHODOLOGY_VERSION = "western-synthesis-method-2026-09-v2"
METHODOLOGY_SOURCE_IDS = (
    "forrest-inner-sky",
    "arroyo-chart-interpretation-handbook",
    "sasportas-twelve-houses",
    "tompkins-aspects-in-astrology",
    "hand-planets-in-transit",
    "george-authentic-self",
    "clifford-heart-of-chart",
    "greene-saturn",
)


@dataclass(frozen=True)
class SynthesisPrinciple:
    source_id: str
    rule: str
    guardrail: str


SYNTHESIS_PRINCIPLES: dict[str, SynthesisPrinciple] = {
    "planet-condition-humility": SynthesisPrinciple(
        source_id="george-authentic-self",
        rule="Chỉ diễn giải mức độ dễ hay khó vận hành khi dữ kiện về điều kiện hành tinh đủ rõ.",
        guardrail="Không biến một vị trí đơn lẻ thành kết luận chắc chắn về con người.",
    ),
    "whole-chart-priority": SynthesisPrinciple(
        source_id="clifford-heart-of-chart",
        rule="Ưu tiên một chủ đề nổi bật và tối đa một tín hiệu hỗ trợ thay vì liệt kê toàn chart.",
        guardrail="Mỗi đoạn phải trả lời một câu hỏi đời thường cụ thể.",
    ),
    "developmental-reframe": SynthesisPrinciple(
        source_id="greene-saturn",
        rule="Đọc điểm căng như một năng lực đang được học qua trải nghiệm và giới hạn.",
        guardrail="Không gọi hành tinh, nhà hay góc là xấu, phạt, định mệnh hoặc điềm báo.",
    ),
}


class InterpretiveLens(StrEnum):
    """A reading angle changes emphasis, never the underlying chart facts."""

    INNER_PATTERN = "inner_pattern"
    RELATIONSHIPS = "relationships"
    WORK = "work"
    REGULATION = "regulation"
    COMMUNICATION = "communication"
    GROWTH = "growth"


class EditorialMode(StrEnum):
    """How today's lens is used; facts remain unchanged."""

    MECHANISM = "mechanism"
    FRICTION = "friction"
    RESOURCE = "resource"
    CONTRAST = "contrast"
    EXPERIMENT = "experiment"


@dataclass(frozen=True)
class DailyEditorialVariant:
    lens: InterpretiveLens
    mode: EditorialMode
    action_slot: int
    reflection_slot: int

    @property
    def signature(self) -> str:
        return (
            f"daily-editorial-v2:{self.lens.value}:{self.mode.value}:"
            f"action-{self.action_slot}:reflection-{self.reflection_slot}"
        )


@dataclass(frozen=True)
class PlanetPerspective:
    protection: str
    relationships: str
    work: str
    regulation: str
    growth_question: str


@dataclass(frozen=True)
class ElementMeaning:
    rhythm: str
    overload: str
    missing_move: str


@dataclass(frozen=True)
class ModalityMeaning:
    tempo: str
    strength: str
    stuck_pattern: str


@dataclass(frozen=True)
class HouseModeMeaning:
    function: str
    watch: str


PLANET_PERSPECTIVES: dict[str, PlanetPerspective] = {
    "sun": PlanetPerspective(
        "tự cầm lái để không thấy mình bị mờ đi",
        "muốn được nhìn nhận đúng với điều mình thật sự coi trọng",
        "cần thấy phần đóng góp của mình rõ ràng và có ý nghĩa",
        "quay lại một lựa chọn mình có quyền quyết",
        "Việc nào là của bạn, và việc nào chỉ đang giúp bạn trông có vẻ ổn?",
    ),
    "moon": PlanetPerspective(
        "thu mình hoặc chăm người khác trước để giữ cảm giác an toàn",
        "cần đủ tin cậy rồi mới nói hết nhu cầu",
        "làm tốt hơn khi khối lượng công việc không bắt cơ thể phải giả vờ ổn",
        "gọi tên cảm giác và nhu cầu thành hai câu riêng",
        "Bạn đang cần được hiểu, được yên, hay được giúp một việc cụ thể?",
    ),
    "mercury": PlanetPerspective(
        "phân tích thêm để tránh nói khi chưa chắc",
        "kết nối bằng câu hỏi, cách gọi tên và trao đổi thông tin",
        "cần bài toán rõ, phản hồi cụ thể và chỗ để nghĩ thành lời",
        "viết câu chính trước rồi mới thêm phần giải thích",
        "Bạn còn thiếu dữ kiện thật, hay đang thiếu can đảm để chốt câu?",
    ),
    "venus": PlanetPerspective(
        "giữ hòa khí hoặc thử lòng để tránh cảm giác không được chọn",
        "tìm sự có qua có lại, gu chung và cách trân trọng có thể cảm nhận được",
        "nhạy với chất lượng hợp tác, thẩm mỹ và mức công sức có được ghi nhận",
        "nói một điều mình thích và một điều mình không muốn tiếp tục",
        "Điều gì khiến bạn thấy được trân trọng mà không cần người khác đoán?",
    ),
    "mars": PlanetPerspective(
        "hành động ngay hoặc dựng ranh giới để không thấy mình bất lực",
        "thể hiện mong muốn qua mức chủ động, cách phản ứng khi bất đồng và cách từ chối",
        "cần mục tiêu có lực cản vừa đủ và quyền tự bắt đầu",
        "tách cơn bực khỏi việc cần làm tiếp theo",
        "Bạn đang bảo vệ điều gì, và cách bảo vệ hiện tại có thật sự hiệu quả?",
    ),
    "jupiter": PlanetPerspective(
        "phóng tầm nhìn ra xa để thoát cảm giác bị bó hẹp",
        "mang vào quan hệ sự hào phóng, niềm tin và mong muốn cùng lớn lên",
        "cần không gian học, thử và nối việc hiện tại với bức tranh lớn",
        "kiểm tra một niềm tin bằng một bằng chứng nhỏ",
        "Khả năng nào đáng thử, và điều gì cần kiểm chứng trước khi đi xa?",
    ),
    "saturn": PlanetPerspective(
        "siết tiêu chuẩn hoặc tự gánh để tránh sai và mất kiểm soát",
        "xây niềm tin qua sự nhất quán, trách nhiệm và ranh giới rõ",
        "mạnh ở việc chịu trách nhiệm nhưng dễ biến mọi thứ thành bài kiểm tra",
        "đặt chuẩn đủ dùng cùng một mốc dừng",
        "Cấu trúc nào đang nâng bạn, cấu trúc nào chỉ đang làm bạn co lại?",
    ),
    "uranus": PlanetPerspective(
        "tách ra hoặc đổi luật để giữ quyền tự chủ",
        "cần khoảng thở, sự thật và quyền không diễn đúng vai cũ",
        "thấy nhanh cách làm khác nhưng có thể đổi trước khi đội nhóm kịp theo",
        "đổi một biến nhỏ thay vì lật cả hệ",
        "Bạn cần tự do khỏi điều gì, và điều gì vẫn đáng được giữ lại?",
    ),
    "neptune": PlanetPerspective(
        "làm mờ ranh giới để giữ hy vọng hoặc tránh một thực tế thô ráp",
        "kết nối qua đồng cảm, tưởng tượng và những điều khó nói thành dữ kiện",
        "hợp việc cần cảm quan nhưng dễ hụt khi mục tiêu và quyền hạn quá mơ hồ",
        "tách điều biết, điều đoán và điều hy vọng",
        "Cảm giác này đang chỉ đường, hoặc đang lấp chỗ cho một thông tin còn thiếu?",
    ),
    "pluto": PlanetPerspective(
        "giữ chặt hoặc đọc thật sâu để không bị đặt vào thế yếu",
        "đòi hỏi độ thật và niềm tin cao, nên khó chịu với sự nửa vời",
        "có sức đi tới lõi vấn đề nhưng dễ biến kiểm soát thành cách tự bảo vệ",
        "chọn một phần có thể buông mà không bỏ rơi mình",
        "Bạn đang cần thay đổi điều gì, hay chỉ đang cố thắng cảm giác bất an?",
    ),
    "chiron": PlanetPerspective(
        "né hoặc phòng thủ quanh một điểm từng bị chạm đau",
        "nhạy với cách người khác gọi tên điểm yếu và nhu cầu được đối xử có ý thức",
        "dễ làm rất tốt điều mình từng phải tự học theo cách khó",
        "đặt tên đúng điểm bị chạm trước khi phản ứng",
        "Phần nào đang thuộc về hiện tại, phần nào là tiếng vọng của lần trước?",
    ),
    "true_node": PlanetPerspective(
        "ép mình phải mới ngay để không bị kéo lại thói quen cũ",
        "học một cách hiện diện và phản ứng chưa thật thuận tay",
        "phát triển qua việc tập năng lực mới ở quy mô có thể thử lại",
        "thử một lựa chọn mới nhưng giữ vòng phản hồi ngắn",
        "Bước mới nhỏ nhất nào đủ thật để bạn học từ nó?",
    ),
    "mean_node": PlanetPerspective(
        "ép mình phải mới ngay để không bị kéo lại thói quen cũ",
        "học một cách hiện diện và phản ứng chưa thật thuận tay",
        "phát triển qua việc tập năng lực mới ở quy mô có thể thử lại",
        "thử một lựa chọn mới nhưng giữ vòng phản hồi ngắn",
        "Bước mới nhỏ nhất nào đủ thật để bạn học từ nó?",
    ),
    "south_node": PlanetPerspective(
        "quay về phản xạ quen vì ít tốn sức và dễ đoán",
        "mang vào quan hệ một kỹ năng cũ hữu ích lẫn một vai cũ có thể đã chật",
        "có năng lực sẵn nhưng dễ dùng nó thay cho việc học cách mới",
        "giữ kỹ năng, bỏ bớt phản xạ tự động",
        "Điều quen thuộc nào vẫn là tài sản, điều nào đã thành nơi trốn?",
    ),
}


CURRENT_FORCES: dict[str, str] = {
    "sun": "nhu cầu tự cầm lái",
    "moon": "nhu cầu thấy đủ an toàn",
    "mercury": "nhu cầu hiểu và nói cho rõ",
    "venus": "nhu cầu được trân trọng và có qua có lại",
    "mars": "lực hành động và dựng ranh giới",
    "jupiter": "lực mở rộng một khả năng",
    "saturn": "lực siết cấu trúc và trách nhiệm",
    "uranus": "lực đổi luật để lấy lại khoảng thở",
    "neptune": "lực làm mềm ranh giới và tăng tưởng tượng",
    "pluto": "lực đào tới lõi và đổi cách kiểm soát",
    "chiron": "độ nhạy quanh một điểm từng bị chạm",
    "true_node": "lực tập một phản ứng mới",
    "mean_node": "lực tập một phản ứng mới",
    "south_node": "lực kéo về phản xạ quen",
}


ELEMENTS: dict[str, ElementMeaning] = {
    "fire": ElementMeaning(
        "cần động lực, ý nghĩa và quyền bắt đầu",
        "phản ứng trước khi kiểm tra mình còn đủ tỉnh táo hay không",
        "đưa thêm dữ kiện và chờ vài phút trước khi quyết định",
    ),
    "earth": ElementMeaning(
        "cần thứ có thể chạm, đo hoặc làm thành bước cụ thể",
        "giữ điều quen chỉ vì nó vẫn chưa hỏng hẳn",
        "cho phép thử nghiệm trước khi mọi thứ hoàn hảo",
    ),
    "air": ElementMeaning(
        "cần ngôn ngữ, góc nhìn và trao đổi để hiểu",
        "ở trong đầu quá lâu nên cảm giác và cơ thể bị bỏ lại",
        "kiểm tra cơ thể và gọi tên một nhu cầu không cần tranh luận",
    ),
    "water": ElementMeaning(
        "cần độ an toàn, kết nối và thời gian để cảm nhận",
        "hấp thụ bầu không khí rồi coi nó là trách nhiệm của mình",
        "đặt một ranh giới có hình dạng và một dữ kiện có thể kiểm tra",
    ),
}


MODALITIES: dict[str, ModalityMeaning] = {
    "cardinal": ModalityMeaning(
        "khởi động và tạo chuyển động",
        "biết mở cửa cho một tiến trình mới",
        "mở quá nhiều cửa nhưng chưa ở lại đủ lâu",
    ),
    "fixed": ModalityMeaning(
        "duy trì và làm sâu",
        "tạo độ bền khi đã tin vào điều mình làm",
        "giữ thế cũ lâu hơn mức còn có ích",
    ),
    "mutable": ModalityMeaning(
        "thích nghi, biên tập và nối các góc nhìn",
        "đổi cách làm khi bối cảnh thay đổi",
        "chỉnh mãi nên khó biết lúc nào đã đủ để chốt",
    ),
}


SIGN_STRUCTURE: dict[str, tuple[str, str]] = {
    "aries": ("fire", "cardinal"),
    "taurus": ("earth", "fixed"),
    "gemini": ("air", "mutable"),
    "cancer": ("water", "cardinal"),
    "leo": ("fire", "fixed"),
    "virgo": ("earth", "mutable"),
    "libra": ("air", "cardinal"),
    "scorpio": ("water", "fixed"),
    "sagittarius": ("fire", "mutable"),
    "capricorn": ("earth", "cardinal"),
    "aquarius": ("air", "fixed"),
    "pisces": ("water", "mutable"),
}


HOUSE_MODES: dict[str, HouseModeMeaning] = {
    "angular": HouseModeMeaning(
        "đưa phản ứng bên trong thành hành động dễ thấy",
        "phản ứng quá nhanh vì mọi thứ có cảm giác đang xảy ra ngay bây giờ",
    ),
    "succedent": HouseModeMeaning(
        "giữ, nuôi và biến một cách làm thành thói quen bền",
        "bám vào cách cũ vì đã đầu tư nhiều vào nó",
    ),
    "cadent": HouseModeMeaning(
        "quan sát, chia nhỏ và đổi cách hiểu vấn đề",
        "ở trong khâu chuẩn bị hoặc diễn giải lâu hơn mức cần thiết",
    ),
}


_HOUSE_MODE_BY_NUMBER = {
    1: "angular",
    2: "succedent",
    3: "cadent",
    4: "angular",
    5: "succedent",
    6: "cadent",
    7: "angular",
    8: "succedent",
    9: "cadent",
    10: "angular",
    11: "succedent",
    12: "cadent",
}


_BACKGROUND_TO_INTERPRETIVE = {
    BackgroundLens.RELATIONSHIPS: InterpretiveLens.RELATIONSHIPS,
    BackgroundLens.COMMUNICATION: InterpretiveLens.COMMUNICATION,
    BackgroundLens.WORK: InterpretiveLens.WORK,
    BackgroundLens.ENERGY: InterpretiveLens.REGULATION,
    BackgroundLens.SELF_CARE: InterpretiveLens.REGULATION,
}


def resolve_interpretive_lens(
    seed: str | None,
    background_lens: BackgroundLens | None,
) -> InterpretiveLens:
    if background_lens is not None:
        return _BACKGROUND_TO_INTERPRETIVE[background_lens]
    values = tuple(InterpretiveLens)
    if seed:
        try:
            local_date = date.fromisoformat(seed.split(":", 1)[0])
        except ValueError:
            pass
        else:
            return values[local_date.toordinal() % len(values)]
    digest = sha256((seed or "evergreen-lens").encode()).digest()
    return values[int.from_bytes(digest[:2], "big") % len(values)]


def resolve_daily_editorial_variant(
    seed: str | None,
    background_lens: BackgroundLens | None,
) -> DailyEditorialVariant:
    """Return one deterministic point in a 630-day semantic editorial cycle.

    The mixed-radix order is deliberate: adjacent local dates change lens first,
    then the editorial question, then the action. We persist none of the user's
    prose or birth data to prevent repetition.
    """

    lens_values = tuple(InterpretiveLens)
    mode_values = tuple(EditorialMode)
    if seed:
        try:
            local_date = date.fromisoformat(seed.split(":", 1)[0])
        except ValueError:
            cycle_day = int.from_bytes(sha256(seed.encode()).digest()[:4], "big")
        else:
            cycle_day = local_date.toordinal()
    else:
        cycle_day = int.from_bytes(sha256(b"evergreen-editorial").digest()[:4], "big")

    if background_lens is None:
        lens = lens_values[cycle_day % len(lens_values)]
        remainder = cycle_day // len(lens_values)
    else:
        lens = _BACKGROUND_TO_INTERPRETIVE[background_lens]
        remainder = cycle_day
    mode = mode_values[remainder % len(mode_values)]
    remainder //= len(mode_values)
    action_slot = remainder % 3
    reflection_slot = (remainder // 3) % 7
    return DailyEditorialVariant(
        lens=lens,
        mode=mode,
        action_slot=action_slot,
        reflection_slot=reflection_slot,
    )


def daily_mixed_radix_slots(seed: str | None, radices: tuple[int, ...]) -> tuple[int, ...]:
    """Map a local date to a stable tuple that repeats only after product(radices)."""

    if any(radix < 1 for radix in radices):
        raise ValueError("Daily editorial radices must all be positive")
    if seed:
        try:
            local_date = date.fromisoformat(seed.split(":", 1)[0])
        except ValueError:
            value = int.from_bytes(sha256(seed.encode()).digest()[:8], "big")
        else:
            value = local_date.toordinal()
    else:
        value = int.from_bytes(sha256(b"evergreen-editorial-slots").digest()[:8], "big")
    slots: list[int] = []
    for radix in radices:
        slots.append(value % radix)
        value //= radix
    return tuple(slots)


def sign_structure(sign: str) -> tuple[ElementMeaning, ModalityMeaning, str, str]:
    element_key, modality_key = SIGN_STRUCTURE.get(sign, SIGN_STRUCTURE["pisces"])
    return ELEMENTS[element_key], MODALITIES[modality_key], element_key, modality_key


def house_mode(house: int) -> tuple[HouseModeMeaning, str]:
    mode_key = _HOUSE_MODE_BY_NUMBER.get(house, "cadent")
    return HOUSE_MODES[mode_key], mode_key
