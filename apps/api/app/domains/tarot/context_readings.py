"""Original Vietnamese prompts for four everyday contexts, not inferred facts.

Each authored row contains core, pitfall, action and a labelled hypothetical
example. Keeping them together makes editorial review easier. The public banks
only separate these fields; they never generate text from ranks or suits.
Energy means everyday effort and attention. Self-care means ordinary care and
personal boundaries. Neither bank assesses health or recommends treatment.
"""

from app.domains.tarot.models import TarotContext

type _Entry = tuple[str, str, str, str]

_WORK: dict[str, _Entry] = {
    "major-fool": (
        "có thể thử một hướng làm mới trước khi cam kết lâu dài",
        "nhận việc chưa rõ yêu cầu chỉ vì muốn thoát công việc cũ",
        "xin một nhiệm vụ thử nhỏ và hỏi tiêu chí hoàn thành",
        "Ví dụ: Bạn muốn đổi vai trò, nhưng có thể thử phụ một dự án trước khi nhận hẳn.",
    ),
    "major-magician": (
        "kỹ năng và công cụ sẵn có đủ để làm bản thử đầu tiên",
        "chuẩn bị hình thức mãi mà chưa tạo được sản phẩm",
        "dùng công cụ quen để làm một bản có thể nhận góp ý",
        "Ví dụ: Khi làm báo cáo, bạn đã có bảng tính quen nhưng vẫn mất buổi tìm phần mềm mới.",
    ),
    "major-high-priestess": (
        "một điểm chưa rõ trong yêu cầu đáng được kiểm tra trước khi làm",
        "coi cảm giác không ổn là bằng chứng đồng nghiệp đang giấu việc",
        "ghi chi tiết chưa khớp và hỏi người phụ trách yêu cầu",
        "Ví dụ: Khi đọc yêu cầu, bạn thấy hai bản ghi thời hạn khác nhau và cần hỏi bản nào "
        "đang dùng.",
    ),
    "major-empress": (
        "điều kiện làm việc thuận tiện giúp ý tưởng được phát triển",
        "chăm chút sản phẩm mãi mà không cho ai dùng thử",
        "nhờ một người dùng thử bản đang có và nghe chỗ họ gặp khó",
        "Ví dụ: Bạn sửa giao diện rất kỹ nhưng chưa xem người mua có tìm được nút đặt hàng không.",
    ),
    "major-emperor": (
        "trách nhiệm và quyền quyết định rõ giúp công việc bớt chồng chéo",
        "kiểm soát từng bước khiến người cùng làm không thể tự xử lý",
        "viết rõ ai phụ trách, ai duyệt và hạn bàn giao đã chốt",
        "Ví dụ: Ba người cùng sửa một tài liệu nhưng chưa có ai chịu trách nhiệm bản cuối.",
    ),
    "major-hierophant": (
        "quy trình và người có kinh nghiệm có thể giúp bạn học nghề chắc hơn",
        "làm theo lệ cũ dù chưa hiểu lý do của nó",
        "hỏi một bước trong quy trình đang bảo vệ điều gì",
        "Ví dụ: Lúc mới vào nhóm, bạn muốn biết vì sao báo giá cần được kiểm tra hai lần.",
    ),
    "major-lovers": (
        "lựa chọn công việc cần hợp với điều bạn coi trọng",
        "chọn chỉ vì lời mời hấp dẫn mà bỏ qua cách làm mình không đồng ý",
        "so hai lựa chọn bằng một tiêu chí bạn không muốn đánh đổi",
        "Ví dụ: Một việc thú vị yêu cầu luôn trực cuối tuần, còn bạn muốn giữ thời gian riêng.",
    ),
    "major-chariot": (
        "mục tiêu rõ giúp bạn tập trung đưa một đầu việc đến đích",
        "thúc tiến độ bằng cách bỏ qua khâu kiểm tra cần thiết",
        "chọn đầu việc ưu tiên và giữ một mốc kiểm tra trước bàn giao",
        "Ví dụ: Khi sắp gửi bản thiết kế, bạn vẫn cần kiểm tra thông số in dù đang muốn bàn "
        "giao ngay.",
    ),
    "major-strength": (
        "bình tĩnh trước áp lực giúp bạn xử lý việc khó mà không công kích ai",
        "chịu đựng yêu cầu quá mức rồi phản ứng gắt khi đã quá tải",
        "nêu phần bạn làm được và phần cần điều chỉnh thời hạn",
        "Ví dụ: Lúc khách yêu cầu sửa gấp, bạn cần báo hôm nay chỉ xử lý được hai mục.",
    ),
    "major-hermit": (
        "thời gian làm sâu giúp bạn tìm ra nguyên nhân thay vì sửa vội",
        "tự nghiên cứu quá lâu mà không báo nhóm đang chờ",
        "đặt một khoảng tập trung và hẹn lúc cập nhật kết quả",
        "Ví dụ: Bạn cần đọc lại số liệu trước cuộc họp, nên báo nhóm khi nào có phân tích.",
    ),
    "major-wheel-of-fortune": (
        "điều kiện bên ngoài thay đổi đòi hỏi kế hoạch có phương án khác",
        "coi một lần trễ do bên ngoài là bằng chứng mình làm kém",
        "cập nhật phần bị ảnh hưởng và chọn việc có thể tiếp tục",
        "Ví dụ: Khi nhà cung cấp dời ngày giao, nhóm vẫn có thể chuẩn bị hướng dẫn sử dụng.",
    ),
    "major-justice": (
        "tiêu chí và dữ kiện rõ giúp đánh giá công sức công bằng hơn",
        "chỉ kể phần mình làm mà bỏ qua cam kết chưa giữ",
        "kiểm tra kết quả theo yêu cầu đã thống nhất",
        "Ví dụ: Bạn muốn trao đổi về đánh giá công việc và mang theo các mốc đã bàn giao.",
    ),
    "major-hanged-man": (
        "tạm đổi cách tiếp cận có thể mở lối cho một việc đang mắc",
        "tiếp tục chờ duyệt mà không hỏi điều gì còn thiếu",
        "hỏi một người về vấn đề này từ phía người dùng",
        "Ví dụ: Nhóm sửa tính năng liên tục nhưng chưa hỏi người dùng có cần tính năng đó không.",
    ),
    "major-death": (
        "khép một đầu việc không còn phù hợp giúp dành chỗ cho ưu tiên mới",
        "giữ dự án chỉ vì đã bỏ nhiều công vào nó",
        "nói rõ phần sẽ dừng và bàn giao những gì còn hữu ích",
        "Ví dụ: Khi chương trình đã kết thúc, bạn vẫn mất giờ cập nhật bảng theo dõi cũ.",
    ),
    "major-temperance": (
        "kết hợp các cách làm vừa phải có thể giải quyết yêu cầu trái nhau",
        "thỏa hiệp đến mức sản phẩm không còn đáp ứng tiêu chí nào",
        "thử một phương án giữ được yêu cầu chính của mỗi bên",
        "Ví dụ: Khi cần giao nhanh mà vẫn chính xác, nhóm thử kiểm tra kỹ phần rủi ro cao trước.",
    ),
    "major-devil": (
        "thói quen nhận việc để được công nhận đáng được xem lại",
        "đồng ý làm ngoài giờ vì sợ mất hình ảnh người luôn sẵn sàng",
        "hỏi mức ưu tiên trước khi nhận thêm một yêu cầu",
        "Ví dụ: Bạn sắp nhận việc tối thứ sáu dù phần đó có thể chờ đến thứ hai.",
    ),
    "major-tower": (
        "thông tin mới có thể làm lộ một giả định sai trong kế hoạch",
        "cố giữ lịch cũ dù điều kiện cần đã không còn",
        "kiểm tra giả định nào sai và báo phần kế hoạch cần sửa",
        "Ví dụ: Khi bản thử không chạy trên thiết bị khách dùng, nhóm cần đổi cách kiểm tra.",
    ),
    "major-star": (
        "một tiến bộ nhỏ có thể giúp bạn tin lại vào hướng làm đang sửa",
        "chỉ hy vọng kết quả tốt lên mà không tiếp tục điều có ích",
        "giữ một thay đổi đã có phản hồi tốt và thử thêm lần nữa",
        "Ví dụ: Sau vài lần bản nháp bị trả lại, bạn có một phần được duyệt để phát triển tiếp.",
    ),
    "major-moon": (
        "yêu cầu thiếu thông tin cần được làm rõ trước khi ước lượng",
        "đoán kỳ vọng của cấp trên rồi làm cả phần chưa được yêu cầu",
        "liệt kê điều đã biết và gửi một câu hỏi về phần còn thiếu",
        "Ví dụ: Yêu cầu chỉ ghi làm cho đẹp hơn, chưa nói người xem cần hiểu điều gì.",
    ),
    "major-sun": (
        "kết quả nhìn thấy được giúp bạn trình bày giá trị công việc rõ hơn",
        "khoe phần thành công mà bỏ qua giới hạn của bản hiện tại",
        "nói về một kết quả tốt và cho xem phần chưa hoàn tất",
        "Ví dụ: Khi giới thiệu bản thử, bạn có thể nêu phần nhập liệu nhanh hơn và phần chưa "
        "xử lý được.",
    ),
    "major-judgement": (
        "nhìn lại cách làm cũ giúp chọn một thay đổi có trách nhiệm",
        "biến lỗi ở một dự án thành kết luận mình không hợp nghề",
        "ghi nguyên nhân có thể sửa và áp dụng vào đầu việc tiếp theo",
        "Ví dụ: Bạn từng trễ vì đợi góp ý sát hạn và muốn đặt mốc góp ý sớm hơn lần này.",
    ),
    "major-world": (
        "hoàn tất và bàn giao đầy đủ là một phần của thành quả",
        "sửa thêm mãi dù sản phẩm đã đạt yêu cầu",
        "kiểm tra danh sách bàn giao rồi đánh dấu việc đã xong",
        "Ví dụ: Khi tài liệu đã được duyệt, bạn vẫn đổi cách trình bày thay vì gửi bản cuối.",
    ),
    "wands-ace": (
        "một ý tưởng mới đáng được thử bằng công việc thực tế",
        "mở thêm dự án ngay lúc hứng thú mà chưa thử khả năng làm",
        "làm một mẫu nhỏ để xem ý tưởng giải quyết được việc gì",
        "Ví dụ: Bạn nghĩ ra cách giới thiệu sản phẩm và thử viết một bài trước khi làm cả loạt.",
    ),
    "wands-2": (
        "cần chọn hướng phát triển thay vì giữ mọi kế hoạch trên giấy",
        "so sánh hai hướng mãi mà không đặt tiêu chí chọn",
        "chọn hướng phù hợp với thời gian và kỹ năng hiện có",
        "Ví dụ: Khi cân nhắc học thiết kế hay quản lý dự án, bạn cần chọn vai trò muốn thử trước.",
    ),
    "wands-3": (
        "theo dõi điều đã khởi động để cân nhắc mở rộng công việc",
        "chờ cơ hội lớn hơn mà không kiểm tra kết quả bước đầu",
        "kiểm tra phản hồi cho đề xuất đã gửi trước khi mở thêm phạm vi",
        "Ví dụ: Dự án đã thử ở một cửa hàng, bạn cần xem kết quả trước khi đề xuất triển khai "
        "rộng.",
    ),
    "wands-4": (
        "một mốc hoàn thành đáng được ghi nhận cùng người đã góp sức",
        "chuyển sang việc mới ngay khiến nhóm không biết phần cũ đã xong",
        "nói rõ mốc đã đạt và cảm ơn người góp phần cụ thể",
        "Ví dụ: Khi đã mở cửa hàng đúng hạn, nhóm vẫn chưa có buổi nhìn lại những gì đã làm được.",
    ),
    "wands-5": (
        "ý kiến khác nhau có thể làm phương án tốt hơn nếu có cách so sánh",
        "để cuộc họp thành nơi ai nói lớn hơn thì được chọn",
        "đặt một tiêu chí chung để thử các phương án đang tranh luận",
        "Ví dụ: Khi hai nhóm thích hai mẫu quảng cáo khác nhau, họ có thể thử trên cùng một "
        "yêu cầu.",
    ),
    "wands-6": (
        "thành quả và công sức xứng đáng được trình bày rõ",
        "chờ lời khen thay cho việc tự ghi nhận kết quả",
        "ghi một kết quả bạn làm được và nhắc đúng người cùng đóng góp",
        "Ví dụ: Khi tổng kết công việc, bạn chưa nhắc thay đổi mình làm đã giảm lỗi giao hàng.",
    ),
    "wands-7": (
        "cần bảo vệ ưu tiên đã chọn trước các yêu cầu phát sinh",
        "coi mọi góp ý là đe dọa rồi từ chối cả ý hữu ích",
        "giải thích lý do giữ phạm vi và xem góp ý nào thật sự cần thiết",
        "Ví dụ: Sát ngày bàn giao có người muốn thêm tính năng không nằm trong yêu cầu ban đầu.",
    ),
    "wands-8": (
        "việc đang tiến nhanh cần thông tin ngắn và kịp thời",
        "nhận lời ngay khi chưa đọc hết thay đổi",
        "hỏi để xác nhận một thay đổi quan trọng trước khi triển khai",
        "Ví dụ: Khi đọc các yêu cầu buổi sáng, bạn thấy hai yêu cầu ghi ngày giao khác nhau.",
    ),
    "wands-9": (
        "kinh nghiệm qua việc khó giúp bạn giữ giới hạn ở chặng cuối",
        "đề phòng đến mức kiểm tra lại cả phần đã được xác nhận",
        "chỉ kiểm tra điểm từng có lỗi và báo phần bạn không thể nhận thêm",
        "Ví dụ: Lúc gần ra mắt, bạn kiểm lại bước thanh toán từng lỗi thay vì làm lại toàn bộ "
        "trang.",
    ),
    "wands-10": (
        "khối lượng đang ôm cần được giảm hoặc chia lại",
        "làm thay mọi người để giữ tiến độ rồi không ai thấy bạn quá tải",
        "viết danh sách đầu việc và đề nghị chuyển một phần cho người phù hợp",
        "Ví dụ: Trong một chiến dịch, bạn đang giữ việc viết nội dung, duyệt ảnh và trả lời khách.",
    ),
    "wands-page": (
        "sự tò mò có thể mở ra một kỹ năng hoặc hướng nghề mới",
        "chỉ xem người khác làm rồi tưởng mình đã thử",
        "xin làm một phần nhỏ trong việc bạn muốn học",
        "Ví dụ: Khi muốn học sản xuất video, bạn có thể thử viết kịch bản cho một đoạn ngắn.",
    ),
    "wands-knight": (
        "sự chủ động giúp một việc đang chậm bắt đầu chuyển động",
        "đổi hướng liên tục khiến người cùng làm không theo kịp",
        "chốt một bước sẽ làm ngay và báo nhóm trước khi đổi kế hoạch",
        "Ví dụ: Bạn muốn chạy chương trình mới ngay nhưng nhóm chưa biết việc cũ có dừng không.",
    ),
    "wands-queen": (
        "tự tin vào kinh nghiệm giúp bạn đưa ý tưởng ra trao đổi",
        "cố tỏ ra luôn giỏi khiến bạn ngại xin góp ý",
        "trình bày ý tưởng của bạn và hỏi một điểm cần cải thiện",
        "Ví dụ: Bạn có cách tổ chức sự kiện mới nhưng đang nhường lượt nói cho người khác.",
    ),
    "wands-king": (
        "dẫn dắt cần một hướng rõ và quyền chủ động cho người cùng làm",
        "đưa tầm nhìn lớn nhưng không xem nhóm có đủ khả năng thực hiện",
        "nêu đích đến và hỏi nhóm cần gì để tự phụ trách phần việc",
        "Ví dụ: Bạn muốn mở thêm kênh bán hàng nhưng cần hỏi nhóm có làm được việc ấy không.",
    ),
    "cups-ace": (
        "cảm hứng với một công việc có thể bắt đầu từ điều bạn thật sự thích",
        "coi cảm giác thích ban đầu là đủ để nhận mọi điều kiện",
        "ghi phần khiến bạn hứng thú và hỏi một yêu cầu thực tế của việc đó",
        "Ví dụ: Bạn thích dự án cộng đồng nhưng chưa biết mỗi người cần dành bao nhiêu giờ để "
        "tham gia.",
    ),
    "cups-2": (
        "hợp tác tốt cần hai bên hiểu và đáp lại nhu cầu công việc của nhau",
        "cho rằng nói chuyện hợp là đã thống nhất cách làm",
        "hỏi để xác nhận mỗi bên sẽ đóng góp gì vào việc chung",
        "Ví dụ: Khi hợp tác với đồng nghiệp hợp ý, bạn vẫn cần chốt ai viết và ai kiểm tra.",
    ),
    "cups-3": (
        "sự hỗ trợ từ đồng nghiệp giúp công việc bớt cô lập",
        "ưu tiên hòa đồng hơn việc góp ý cần thiết",
        "hỏi một đồng nghiệp về phần bạn chưa chắc",
        "Ví dụ: Bạn có thể nhờ nhóm đọc thử bài giới thiệu trước khi gửi cho khách.",
    ),
    "cups-4": (
        "thiếu hứng thú là dịp xem lại nhiệm vụ nào còn đáng quan tâm",
        "gạt mọi đề nghị vì thấy chúng giống việc cũ",
        "kiểm tra yêu cầu của một cơ hội trước khi quyết định không nhận",
        "Ví dụ: Bạn chán việc nhập liệu nên bỏ qua lời mời thử cải tiến chính quy trình đó.",
    ),
    "cups-5": (
        "một kết quả hụt cần được nhìn nhận cùng phần còn có thể dùng",
        "coi một đề xuất bị từ chối là toàn bộ công sức vô ích",
        "tách phần không đạt khỏi tài liệu hoặc kỹ năng có thể giữ lại",
        "Ví dụ: Khi khách không chọn phương án của bạn, bản nghiên cứu vẫn có thể giúp dự án khác.",
    ),
    "cups-6": (
        "kinh nghiệm cũ có thể hữu ích khi được xét trong điều kiện hiện tại",
        "lặp cách từng thành công mà không xem yêu cầu mới",
        "so một cách làm cũ với nhu cầu của công việc lần này",
        "Ví dụ: Khi dùng mẫu báo cáo quen, bạn nhận ra khách mới cần số liệu theo tuần.",
    ),
    "cups-7": (
        "nhiều hướng nghề hấp dẫn cần được lọc bằng việc thực tế",
        "thích hình ảnh của một nghề hơn công việc hằng ngày của nó",
        "hỏi người đang làm nghề về một ngày làm việc bình thường",
        "Ví dụ: Bạn thích làm tự do nhưng chưa xem mình sẽ tìm khách và quản lý lịch ra sao.",
    ),
    "cups-8": (
        "cần xem công việc hiện tại còn đáp ứng điều bạn mong muốn không",
        "bỏ hướng đang làm ngay khi hết hào hứng mà chưa hiểu phần thiếu",
        "ghi điều còn thiếu và thử trao đổi về một thay đổi trong vai trò",
        "Ví dụ: Công việc vẫn ổn nhưng bạn muốn học thêm thay vì lặp một nhiệm vụ mãi.",
    ),
    "cups-9": (
        "biết thế nào là kết quả đủ tốt giúp bạn làm việc có điểm dừng",
        "chỉ dùng lời khen bên ngoài để quyết định mình đã làm tốt chưa",
        "đặt một tiêu chí hoàn thành mà bạn có thể tự kiểm tra",
        "Ví dụ: Khi đã giải quyết đủ yêu cầu, bạn vẫn đợi khách khen mới thấy hài lòng.",
    ),
    "cups-10": (
        "môi trường làm việc phù hợp cho phép mọi người vừa hợp tác vừa nói thật",
        "giữ hình ảnh nhóm hòa thuận bằng cách né vấn đề",
        "hỏi nhóm một điều cần thay đổi để cùng làm thoải mái hơn",
        "Ví dụ: Nhóm vui vẻ trong cuộc họp nhưng vẫn cần nói về việc giao gấp cuối ngày.",
    ),
    "cups-page": (
        "một ý tưởng còn non có thể được học qua góp ý cởi mở",
        "xem lời sửa bản thử như lời đánh giá con người mình",
        "gửi bản nháp và hỏi một điểm cụ thể để học",
        "Ví dụ: Lúc viết bài đầu tiên cho nhóm, bạn muốn được góp ý về cách mở đầu.",
    ),
    "cups-knight": (
        "sự thuyết phục có ích khi đề xuất đi cùng khả năng thực hiện",
        "hứa một sản phẩm đẹp hơn mức thời gian cho phép",
        "viết một đề xuất kèm phần bạn có thể bàn giao thật",
        "Ví dụ: Khi đề xuất video cho khách, bạn cần nói rõ chỉ có thể quay một địa điểm.",
    ),
    "cups-queen": (
        "hiểu khó khăn của đồng nghiệp giúp hỗ trợ đúng phần họ cần",
        "nhận luôn việc của người khác vì thấy họ đang buồn hoặc căng",
        "hỏi họ cần góp ý hay hỗ trợ một đầu việc cụ thể",
        "Ví dụ: Khi đồng nghiệp quá tải, bạn có thể giúp rà tài liệu thay vì nhận cả dự án.",
    ),
    "cups-king": (
        "giữ bình tĩnh giúp dẫn dắt nhóm qua bất đồng và đưa ra quyết định",
        "tỏ ra ổn đến mức nhóm không biết điều gì đang gây khó cho bạn",
        "nói điều bạn lo về công việc rồi chọn cách xử lý dựa trên dữ kiện",
        "Ví dụ: Nhóm bất đồng về cách chia việc, bạn nêu áp lực đang có mà không trách người "
        "góp ý.",
    ),
    "swords-ace": (
        "một vấn đề được gọi đúng tên giúp công việc có hướng giải quyết",
        "nói lỗi quá chung khiến người thực hiện không biết sửa đâu",
        "viết vấn đề, bằng chứng và kết quả cần đạt trong ba câu rõ",
        "Ví dụ: Khi góp ý báo cáo, bạn chỉ ra bảng thiếu đơn vị thay vì nói cả bản khó đọc.",
    ),
    "swords-2": (
        "quyết định đang bị giữ lại vì hai phương án đều có cái giá",
        "đợi mọi rủi ro biến mất rồi mới chọn",
        "xác định dữ kiện còn thiếu có thật sự đổi được lựa chọn không",
        "Ví dụ: Khi gần hạn giao, bạn phải chọn làm ít tính năng hơn hoặc xin thêm thời gian.",
    ),
    "swords-3": (
        "góp ý khó nghe cần được tách khỏi cảm giác bị đánh giá thấp",
        "bỏ qua cả góp ý hữu ích vì cách người nói làm mình buồn",
        "chọn một điểm có thể sửa và trao đổi riêng về cách góp ý",
        "Ví dụ: Lúc bản trình bày bị chê trước nhóm, bạn vẫn có thể hỏi rõ phần số liệu sai.",
    ),
    "swords-4": (
        "tạm ngừng xử lý giúp quay lại một bài toán với đầu óc bớt mệt",
        "ngồi trước màn hình thêm dù không còn kiểm tra được lỗi",
        "lưu việc đang làm và đặt giờ quay lại sau một khoảng nghỉ",
        "Ví dụ: Bạn đọc cùng một bảng nhiều lần mà vẫn bỏ sót dòng nên cần rời bàn một lúc.",
    ),
    "swords-5": (
        "thắng tranh luận chưa chắc giải quyết được việc chung",
        "chỉ ra lỗi của đồng nghiệp để bảo vệ phần mình",
        "đưa cuộc trao đổi về việc cần sửa và người sẽ xử lý",
        "Ví dụ: Cả nhóm tranh ai làm trễ trong khi vẫn chưa chốt cách bàn giao cho khách.",
    ),
    "swords-6": (
        "chuyển sang cách làm bớt vướng cần một bước bàn giao rõ",
        "đổi công cụ rồi để thông tin quan trọng ở hệ thống cũ",
        "chọn phần cần chuyển và hướng dẫn người tiếp nhận cách dùng",
        "Ví dụ: Khi đổi nơi lưu tài liệu, nhóm cần giữ đường dẫn đến các bản đã duyệt.",
    ),
    "swords-7": (
        "cách làm khéo vẫn cần minh bạch với người chịu ảnh hưởng",
        "né báo tin chậm tiến độ để tránh bị hỏi",
        "nói rõ phần đang chậm và đề nghị phương án xử lý thực tế",
        "Ví dụ: Lúc gửi bản chưa kiểm tra, bạn đang định không ghi rõ phần còn thiếu.",
    ),
    "swords-8": (
        "giới hạn công việc cần được kiểm tra thay vì mặc định không thể đổi",
        "tự cho rằng không được hỏi lại yêu cầu",
        "hỏi xem phạm vi hoặc thời hạn có phần nào có thể điều chỉnh",
        "Ví dụ: Bạn nghĩ phải làm hết trong hôm nay nhưng chưa hỏi đầu việc nào cần trước.",
    ),
    "swords-9": (
        "lo về kết quả có thể khiến bạn kiểm lại việc vượt quá mức cần thiết",
        "dùng thêm giờ để trấn an thay vì sửa một lỗi xác định",
        "kiểm theo danh sách đã chọn rồi dừng khi không còn lỗi cần xử lý",
        "Ví dụ: Bạn mở lại thư đã gửi nhiều lần dù không có thông tin mới để sửa.",
    ),
    "swords-10": (
        "một cách làm đã hết khả năng tiếp tục cần được khép lại rõ ràng",
        "cố cứu mọi phần để tránh thừa nhận kế hoạch không đạt",
        "viết phần phải dừng và bước xử lý hậu quả nằm trong trách nhiệm của bạn",
        "Ví dụ: Khi dự án bị hủy, bạn cần bàn giao tài liệu thay vì tiếp tục làm bản ra mắt.",
    ),
    "swords-page": (
        "câu hỏi và việc kiểm chứng giúp bạn học yêu cầu chính xác hơn",
        "hỏi liên tiếp nhưng chưa đọc tài liệu đã có",
        "đọc yêu cầu rồi hỏi một chi tiết chưa có câu trả lời",
        "Ví dụ: Bạn chưa hiểu cách tính số đơn và kiểm định nghĩa trước khi phân tích.",
    ),
    "swords-knight": (
        "khả năng xử lý nhanh cần đi cùng việc nghe đủ yêu cầu",
        "sửa ngay theo ý mình rồi tạo thêm lỗi cho phần liên quan",
        "hỏi để xác nhận phạm vi thay đổi trước khi bắt tay xử lý",
        "Ví dụ: Khi đổi tên một mục, bạn cần xem báo cáo khác có dùng tên ấy không.",
    ),
    "swords-queen": (
        "góp ý rõ và giới hạn minh bạch giúp công việc bớt nhập nhằng",
        "dùng lời sắc đến mức người nghe chỉ nhớ cảm giác bị chê",
        "nói về lỗi ở sản phẩm và yêu cầu sửa, không đánh giá người làm",
        "Ví dụ: Bạn cần trả bản nháp vì thiếu số liệu chứ không cần nói người viết cẩu thả.",
    ),
    "swords-king": (
        "quyết định có căn cứ cần tiêu chí nhất quán và trách nhiệm rõ",
        "áp tiêu chí của mình mà không giải thích cho người thực hiện",
        "công bố tiêu chí chọn và lý do của quyết định",
        "Ví dụ: Khi duyệt nhà cung cấp, bạn có thể đối chiếu thời gian giao với yêu cầu đã chốt.",
    ),
    "pentacles-ace": (
        "một cơ hội cụ thể cần lịch, công cụ và điều kiện thực hiện",
        "nhận lời trước khi biết nguồn lực mình phải bỏ ra",
        "hỏi phạm vi và thời gian cần dành cho nhiệm vụ đầu tiên",
        "Ví dụ: Bạn được mời làm một đầu việc mới nhưng chưa biết có ai hướng dẫn không.",
    ),
    "pentacles-2": (
        "hai đầu việc cần được sắp xếp theo ưu tiên và thời hạn thật",
        "đổi qua lại liên tục khiến cả hai đều chưa xong",
        "đặt một khoảng làm riêng cho việc cần bàn giao trước",
        "Ví dụ: Khi vừa trả lời khách vừa nhập hóa đơn, bạn liên tục phải đọc lại từ đầu.",
    ),
    "pentacles-3": (
        "chuyên môn của từng người cần được ghép theo một tiêu chuẩn chung",
        "làm tốt phần riêng nhưng không kiểm tra chỗ bàn giao",
        "thống nhất tiêu chuẩn và xem thử một phần sản phẩm cùng nhau",
        "Ví dụ: Người viết, người thiết kế và người in cần thống nhất kích thước trước khi làm.",
    ),
    "pentacles-4": (
        "giữ nguồn lực ổn định cần phân biệt khoản dự phòng với việc giữ quá chặt",
        "không chia sẻ công cụ khiến cả nhóm phải làm lại",
        "xác định phần cần giữ và phần có thể cho người cùng làm sử dụng",
        "Ví dụ: Bạn giữ mẫu báo cáo trong máy riêng khiến người cùng làm phải tạo lại một mẫu "
        "tương tự.",
    ),
    "pentacles-5": (
        "thiếu điều kiện làm việc là nhu cầu hỗ trợ đáng được nói rõ",
        "giấu khó khăn vì sợ bị xem là không đủ năng lực",
        "nói rõ công cụ hoặc hướng dẫn cụ thể bạn đang thiếu",
        "Ví dụ: Khi chưa có quyền mở tài liệu cần dùng, bạn vẫn cố làm bằng bản cũ.",
    ),
    "pentacles-6": (
        "phân bổ nguồn lực công bằng giúp người cần hỗ trợ có thể làm tiếp",
        "giúp theo cảm tính mà không rõ mức hỗ trợ và trách nhiệm",
        "hỏi ai cần hỗ trợ gì và thống nhất thời gian bạn có thể dành",
        "Ví dụ: Bạn có hai giờ để giúp nhóm, nên cần chọn đầu việc đang thiếu người nhất.",
    ),
    "pentacles-7": (
        "công sức đã đầu tư cần được xem lại bằng dấu hiệu tiến triển",
        "tiếp tục một cách làm chỉ vì đã làm lâu",
        "đặt mốc đánh giá và xem một kết quả có thể quan sát",
        "Ví dụ: Bạn đã thử kênh bán hàng một tháng và cần xem số yêu cầu thật trước khi làm tiếp.",
    ),
    "pentacles-8": (
        "luyện kỹ năng qua từng lần sửa giúp chất lượng công việc chắc hơn",
        "lặp thao tác nhiều lần mà không xem mình đang sai ở đâu",
        "chọn một lỗi nhỏ để sửa trong lượt thực hành tiếp theo",
        "Ví dụ: Khi luyện trình bày số liệu, bạn tập ghi đúng đơn vị ở mỗi bảng.",
    ),
    "pentacles-9": (
        "khả năng tự làm tốt cho phép bạn chủ động chọn cách làm phù hợp",
        "tự lập đến mức không dùng sự hỗ trợ đang có",
        "ghi phần có thể tự phụ trách và phần nên nhờ kiểm tra",
        "Ví dụ: Bạn tự quản lý một dự án nhỏ nhưng vẫn có thể nhờ người khác rà bản cuối.",
    ),
    "pentacles-10": (
        "kết quả bền cần kiến thức và hệ thống không phụ thuộc một người",
        "coi cách làm lâu năm là đủ mà không lưu hướng dẫn",
        "viết lại một quy trình để người tiếp theo có thể sử dụng",
        "Ví dụ: Cửa hàng làm việc suôn sẻ nhưng chỉ một người biết cách xử lý đơn đổi trả.",
    ),
    "pentacles-page": (
        "học một kỹ năng thực tế bắt đầu từ bài tập vừa sức",
        "gom nhiều khóa học mà chưa làm bài đầu tiên",
        "hoàn thành một bài tập và xin góp ý đúng kỹ năng đang học",
        "Ví dụ: Khi học bảng tính, bạn thử lập danh sách theo dõi đơn cho một tuần.",
    ),
    "pentacles-knight": (
        "tiến độ đáng tin được tạo bằng việc giữ các cam kết nhỏ",
        "bám quy trình đến mức bỏ qua thay đổi trong yêu cầu",
        "giữ lịch bàn giao và kiểm một bước có còn cần thiết không",
        "Ví dụ: Khi gửi báo cáo thứ sáu, bạn cần bỏ phần khách không còn dùng nữa.",
    ),
    "pentacles-queen": (
        "chăm điều kiện thực tế giúp nhóm làm việc mà không phải xoay xở thiếu thốn",
        "lo hậu cần cho tất cả rồi không còn thời gian cho phần mình",
        "chuẩn bị điều thiết yếu và chia người phụ trách phần còn lại",
        "Ví dụ: Bạn lo phòng họp và tài liệu, nhưng có thể giao người khác kiểm thiết bị.",
    ),
    "pentacles-king": (
        "quản lý nguồn lực tốt cần mức cam kết ổn định và giới hạn rõ",
        "dùng quyền giữ ngân sách để quyết định thay mọi chuyên môn",
        "nói rõ nguồn lực có thể dùng và để người phụ trách đề xuất cách thực hiện",
        "Ví dụ: Bạn có quyền duyệt thiết bị nhưng cần nghe người sử dụng về nhu cầu thật.",
    ),
}

_COMMUNICATION: dict[str, _Entry] = {
    "major-fool": (
        "có thể mở lời dù chưa biết cuộc trao đổi sẽ diễn ra thế nào",
        "nói quá nhiều chuyện riêng khi chưa rõ mình muốn chia sẻ đến đâu",
        "bắt đầu bằng một câu hỏi dễ trả lời và giữ quyền không kể thêm",
        "Ví dụ: Bạn muốn bắt chuyện với người mới trong lớp và hỏi về bài tập hôm nay.",
    ),
    "major-magician": (
        "chọn cách diễn đạt phù hợp giúp người nghe hiểu đúng ý bạn",
        "nói khéo để được đồng ý mà bỏ mất điều mình thật sự muốn",
        "viết câu chính trước rồi thêm thông tin cần thiết để người nghe hiểu",
        "Ví dụ: Bạn viết một lời nhờ dài nhưng chưa nói rõ muốn người nhận giúp việc gì.",
    ),
    "major-high-priestess": (
        "điều chưa được nói rõ cần được nghe thêm thay vì đoán hộ",
        "lấy một khoảng im lặng làm bằng chứng về ý định người khác",
        "hỏi người kia có muốn giải thích thêm điều vừa nói không",
        "Ví dụ: Một người ngừng giữa câu, bạn có thể chờ hoặc hỏi thay vì tự điền ý.",
    ),
    "major-empress": (
        "sự quan tâm cụ thể có thể làm cuộc trò chuyện dễ mở hơn",
        "nói lời an ủi ngay khiến người kể chưa kịp nói hết",
        "chờ người kia kể xong rồi nhắc một điều bạn đã nghe",
        "Ví dụ: Người bạn đang kể ngày không vui có thể chưa cần một danh sách cách giải quyết.",
    ),
    "major-emperor": (
        "mục đích và giới hạn rõ giúp cuộc trao đổi không lan man",
        "đặt luật nói chuyện mà không cho người khác góp ý",
        "hỏi để cùng chốt chủ đề và thời gian có thể nói chuyện",
        "Ví dụ: Gia đình cần bàn việc nhà nhưng cuộc nói chuyện cứ chuyển sang chuyện cũ.",
    ),
    "major-hierophant": (
        "cách hiểu chung về từ ngữ giúp tránh nói giống mà hiểu khác",
        "dùng quy tắc giao tiếp quen như điều ai cũng phải biết",
        "hỏi người nghe hiểu một từ quan trọng trong thỏa thuận thế nào",
        "Ví dụ: Hai người đều nói sẽ phản hồi sớm nhưng một bên hiểu là hôm nay, bên kia là "
        "tuần sau.",
    ),
    "major-lovers": (
        "nói điều mình coi trọng giúp lựa chọn chung có cơ sở",
        "đồng ý cho dễ chịu rồi mong người khác đoán mình không muốn",
        "nêu một điều bạn muốn giữ khi cùng chọn phương án",
        "Ví dụ: Bạn muốn chuyến đi đơn giản nhưng cứ gật đầu khi nhóm đề nghị lịch kín cả ngày.",
    ),
    "major-chariot": (
        "cuộc nói chuyện có thể tiến tới một yêu cầu rõ thay vì vòng quanh",
        "thúc người nghe chốt ngay theo tốc độ của mình",
        "nói kết quả bạn mong và hỏi họ cần gì để trả lời",
        "Ví dụ: Bạn muốn chốt ngày gặp, còn người kia cần kiểm tra lịch trước.",
    ),
    "major-strength": (
        "bạn có thể nói điều khó chịu bằng lời rõ mà không công kích",
        "nhịn đến khi lời nói trở nên nặng hơn vấn đề ban đầu",
        "nêu việc làm bạn khó chịu và một thay đổi bạn muốn đề nghị",
        "Ví dụ: Người cùng nhà bật loa lúc khuya, bạn có thể nói về giờ nghỉ thay vì chê tính họ.",
    ),
    "major-hermit": (
        "nghĩ riêng một lúc giúp bạn biết câu nào thật sự cần nói",
        "biến thời gian suy nghĩ thành im lặng không báo trước",
        "nói rằng bạn cần nghĩ thêm và hẹn lúc trả lời được",
        "Ví dụ: Khi chưa biết nhận lời mời thế nào, bạn có thể xin trả lời vào chiều mai.",
    ),
    "major-wheel-of-fortune": (
        "cách liên lạc có thể cần đổi khi lịch sinh hoạt thay đổi",
        "coi một lần lỡ cuộc gọi là dấu hiệu không được tôn trọng",
        "hỏi khung giờ phù hợp hiện tại thay vì giữ lịch gọi cũ",
        "Ví dụ: Khi bạn của bạn đổi ca làm, giờ gọi quen không còn thuận tiện cho họ.",
    ),
    "major-justice": (
        "trao đổi công bằng cần phân biệt việc đã xảy ra với cách mình hiểu",
        "chỉ kể chi tiết có lợi cho lập luận của mình",
        "nói về sự việc cụ thể và nhận phần trách nhiệm của bạn nếu có",
        "Ví dụ: Bạn nói người kia đổi hẹn nhưng cũng cần nhắc lần mình báo muộn.",
    ),
    "major-hanged-man": (
        "nghe cách người khác hiểu có thể đổi nghĩa của một câu gây vướng",
        "lặp lời giải thích cũ thật nhiều mà không hỏi họ đang hiểu gì",
        "hỏi người nghe đã hiểu câu của bạn thế nào rồi làm rõ chỗ lệch",
        "Ví dụ: Bạn nói tùy bạn để nhường chọn, còn người nghe tưởng bạn không muốn tham gia.",
    ),
    "major-death": (
        "một cách nói không còn hữu ích có thể được dừng lại",
        "khơi lại cùng lời trách mỗi lần có chuyện mới",
        "thống nhất bỏ một cách nói cũ và thử câu đề nghị cụ thể",
        "Ví dụ: Hai người muốn bỏ câu lúc nào bạn cũng vậy khi bàn việc trễ hẹn.",
    ),
    "major-temperance": (
        "điều chỉnh cách nói và cách nghe giúp hai bên theo kịp nhau",
        "nói nhẹ đến mức người nghe không biết yêu cầu là gì",
        "nói một ý rồi để người kia trả lời trước khi chuyển ý tiếp",
        "Ví dụ: Bạn muốn nói nhiều chuyện, còn người nghe cần từng vấn đề riêng để trả lời.",
    ),
    "major-devil": (
        "cần nhận ra lúc mình nói chỉ để giữ sự đồng ý của người khác",
        "dùng cảm giác có lỗi để buộc người nghe làm theo",
        "nói điều muốn nhờ với chỗ cho lời từ chối, không kèm lời trách",
        "Ví dụ: Bạn muốn nhờ giúp nhưng có thể hỏi thẳng thay vì nhắc người kia từng được mình "
        "giúp.",
    ),
    "major-tower": (
        "một thông tin bất ngờ cần được xác nhận trước khi phản ứng",
        "đáp trả ngay khi mới nghe một phần câu chuyện",
        "hỏi lại điều vừa nghe và tạm dừng nếu chưa thể nói bình tĩnh",
        "Ví dụ: Bạn nghe kế hoạch chung bị đổi qua lời kể lại và cần hỏi người phụ trách.",
    ),
    "major-star": (
        "một lời nói chân thành có thể mở lại cuộc trao đổi sau thất vọng",
        "hy vọng người khác tự hiểu mà không nói điều cần thay đổi",
        "đề nghị một cách nói chuyện khác cho lần trao đổi tới",
        "Ví dụ: Sau lần hiểu lầm, bạn muốn thử nói trực tiếp thay vì nhắn những câu ngắn.",
    ),
    "major-moon": (
        "câu thiếu ngữ cảnh cần được hỏi lại trước khi gán ý nghĩa",
        "dùng nỗi lo để đoán giọng điệu trong tin nhắn",
        "hỏi về đúng chi tiết chưa rõ mà không gán động cơ",
        "Ví dụ: Tin nhắn chỉ có chữ được khiến bạn băn khoăn nhưng chưa nói lên người gửi nghĩ gì.",
    ),
    "major-sun": (
        "nói thật điều vui và điều muốn giúp người nghe hiểu bạn dễ hơn",
        "đùa cho vui đến mức che mất điều cần nói nghiêm túc",
        "nói cụ thể một điều bạn thích, không để người nghe phải đoán",
        "Ví dụ: Bạn rất thích món quà nhưng chỉ trêu nên người tặng không biết bạn thấy vui.",
    ),
    "major-judgement": (
        "nhìn lại lời mình từng nói giúp sửa cách trao đổi ở lần này",
        "xin lỗi chung chung mà không nhận đúng điều gây khó chịu",
        "nhắc việc mình đã nói và nói rõ lần tới sẽ làm khác thế nào",
        "Ví dụ: Bạn từng ngắt lời trong cuộc gọi và muốn để người kia nói xong trước khi góp ý.",
    ),
    "major-world": (
        "kết thúc cuộc trao đổi rõ giúp mọi người biết đã thống nhất điều gì",
        "nói thêm chuyện mới khi người nghe tưởng đã chốt xong",
        "nói lại điều đã đồng ý và để phần khác cho lần sau",
        "Ví dụ: Lúc cuộc gọi đã chọn được ngày đi, hai bên vẫn chưa xác nhận lại quyết định.",
    ),
    "wands-ace": (
        "hứng thú có thể trở thành một lời mời dễ hưởng ứng",
        "gửi liên tiếp nhiều ý tưởng khiến người nhận không biết chọn gì",
        "đưa một lời mời cụ thể và hỏi người kia có hứng thú không",
        "Ví dụ: Khi muốn rủ nhóm thử trò chơi mới, bạn gửi một lời mời cho tối thứ bảy.",
    ),
    "wands-2": (
        "cân nhắc trước khi mở lời giúp bạn biết mình muốn hỏi hay muốn đề nghị",
        "soạn nhiều phiên bản mà không chọn câu chính",
        "chọn một câu nói rõ mong muốn và gửi khi bạn sẵn sàng",
        "Ví dụ: Bạn muốn đề nghị đổi lịch nhưng cứ sửa phần mở đầu mà chưa nêu ngày mới.",
    ),
    "wands-3": (
        "sau khi nói rõ lời đề nghị, cần dành thời gian cho phản hồi",
        "chờ người nghe tự biết lúc nào và bằng cách nào nên trả lời",
        "hẹn một lúc hỏi lại nếu chưa có phản hồi, không nhắn dồn",
        "Ví dụ: Bạn đã gửi tin nhắn rủ gặp và có thể hỏi lúc nào người kia tiện trả lời.",
    ),
    "wands-4": (
        "lời chào đón giúp người tham gia biết mình có chỗ trong cuộc trò chuyện",
        "chỉ nói chuyện nội bộ khiến người mới khó góp lời",
        "giới thiệu một người mới và mở một câu hỏi họ có thể tham gia",
        "Ví dụ: Nhóm bạn gặp nhau có một người mới chưa biết câu chuyện mọi người đang nhắc.",
    ),
    "wands-5": (
        "nhiều ý kiến cần lượt nói để trở thành trao đổi có ích",
        "ngắt lời để bảo vệ ý mình làm người khác phải nói lớn hơn",
        "đề nghị mỗi người nói hết một ý trước khi phản hồi",
        "Ví dụ: Khi cùng chọn nơi ăn, mọi người nói cùng lúc nên chưa nghe rõ lựa chọn nào.",
    ),
    "wands-6": (
        "ghi nhận cụ thể giúp người nghe biết công sức của họ được nhìn thấy",
        "khen quá chung khiến lời cảm ơn không nói được điều gì",
        "nhắc một việc người kia đã làm và nó giúp bạn ra sao",
        "Ví dụ: Bạn muốn cảm ơn người đã đón mình đúng giờ khi buổi gặp kết thúc muộn.",
    ),
    "wands-7": (
        "ý kiến riêng có thể được giữ mà không phải bác bỏ người khác",
        "nghe câu hỏi như lời công kích rồi trả lời phòng thủ",
        "nói lý do lựa chọn của bạn và hỏi họ đang băn khoăn điểm nào",
        "Ví dụ: Một người hỏi vì sao bạn không đi cùng, bạn có thể giải thích thay vì đáp gắt.",
    ),
    "wands-8": (
        "trao đổi nhanh cần câu ngắn và thông tin đủ để trả lời",
        "gửi nhiều mẩu tin rời khiến ý chính bị trôi",
        "viết một tin đủ thông tin và nêu câu cần được trả lời",
        "Ví dụ: Nhóm nhắn liên tục lúc hẹn gặp nhưng địa điểm vẫn nằm rải trong nhiều tin.",
    ),
    "wands-9": (
        "dè chừng sau hiểu lầm là điều có thể nói thay vì giấu trong giọng điệu",
        "mang chuyện cũ vào để nghi ngờ mọi câu mới",
        "nêu chi tiết bạn cần làm rõ trong lần nói chuyện hiện tại",
        "Ví dụ: Bạn từng bị đổi hẹn muộn và lần này muốn hỏi cách báo nếu lịch thay đổi.",
    ),
    "wands-10": (
        "gánh giữ liên lạc có thể được chia thay vì một người luôn phải mở lời",
        "vừa hỏi vừa giải thích hộ khiến người khác không có lượt góp ý",
        "nói một câu hỏi rồi để người nghe tự trả lời",
        "Ví dụ: Bạn nhắn trong nhóm và tự đưa luôn mọi câu trả lời trước khi ai kịp phản hồi.",
    ),
    "wands-page": (
        "câu hỏi tò mò thật giúp cuộc trò chuyện có điều mới để khám phá",
        "hỏi để gây ấn tượng hơn là muốn nghe câu trả lời",
        "hỏi một chi tiết bạn muốn biết và nghe hết phần kể",
        "Ví dụ: Bạn nghe một người nhắc sở thích trồng cây và muốn biết họ bắt đầu từ cây nào.",
    ),
    "wands-knight": (
        "nhiệt tình giúp mở chuyện nhưng cần chừa chỗ cho người nghe",
        "nói liền một mạch rồi tưởng im lặng là đồng ý",
        "dừng sau đề nghị đầu tiên và hỏi người kia thấy thế nào",
        "Ví dụ: Bạn hào hứng kể kế hoạch đi chơi trong khi người nghe chưa kịp nói lịch của họ.",
    ),
    "wands-queen": (
        "sự tự tin giúp bạn nói bằng giọng của mình thay vì cố diễn",
        "cố giữ mọi sự chú ý khiến câu chuyện của người khác bị bỏ qua",
        "nói điều bạn muốn chia sẻ rồi mời một người khác góp chuyện",
        "Ví dụ: Khi có chuyện vui muốn kể, bạn cũng muốn nghe ngày hôm nay của những người "
        "trong buổi gặp.",
    ),
    "wands-king": (
        "nói rõ hướng mong muốn giúp mọi người cùng bàn bước tiếp theo",
        "trình bày ý mình như quyết định đã thay tất cả",
        "đưa đề nghị và hỏi ai muốn sửa hoặc bổ sung trước khi chốt",
        "Ví dụ: Bạn muốn nhóm gặp hằng tháng nhưng cần hỏi lịch và mong muốn của từng người.",
    ),
    "cups-ace": (
        "một cảm xúc mới có thể được nói ra mà chưa cần giải thích hết",
        "kể quá nhiều để đòi một phản ứng tương tự ngay",
        "nói một cảm xúc bằng câu về mình rồi để người nghe đáp lại",
        "Ví dụ: Bạn thấy vui sau buổi gặp và có thể nói điều đó mà chưa hỏi người kia có giống "
        "mình không.",
    ),
    "cups-2": (
        "đối thoại cần cả nói thật lẫn kiểm tra mình đã hiểu đúng người kia",
        "đồng ý quá nhanh chỉ vì muốn được xem là hợp ý",
        "nhắc lại điều bạn hiểu rồi hỏi có đúng ý người nói không",
        "Ví dụ: Hai người đang chọn cách liên lạc và cần hiểu mỗi bên thấy thuận tiện ra sao.",
    ),
    "cups-3": (
        "chuyện trò trong nhóm có thể tạo gần gũi khi ai cũng được góp lời",
        "kể chuyện riêng của người vắng mặt để cả nhóm vui",
        "chọn chuyện của mình để kể và không tiết lộ chuyện riêng của người khác",
        "Ví dụ: Lúc ăn cùng nhóm, bạn có chuyện vui nhưng một chi tiết thuộc đời riêng của bạn "
        "mình.",
    ),
    "cups-4": (
        "chưa muốn trò chuyện là điều có thể báo thay vì miễn cưỡng đáp",
        "trả lời cụt mà mong người khác tự hiểu mình cần yên tĩnh",
        "nói rằng lúc này bạn chưa muốn nói chuyện và báo nếu muốn hẹn lại",
        "Ví dụ: Bạn được gọi lúc đang cần ở một mình và có thể xin trao đổi vào hôm khác.",
    ),
    "cups-5": (
        "thất vọng cần được nói về đúng chuyện thay vì gom thành lời trách",
        "dùng một lần hụt hẫng để phủ nhận mọi quan tâm đã có",
        "nói về việc khiến bạn thất vọng và điều bạn mong ở lần tới",
        "Ví dụ: Một người quên lời hẹn, bạn muốn nói về lần đó chứ không kết luận họ luôn vô tâm.",
    ),
    "cups-6": (
        "ký ức chung có thể mở chuyện nếu người nghe cũng muốn nhắc lại",
        "coi chuyện ngày xưa là lý do người khác phải đồng ý hôm nay",
        "hỏi người kia có muốn kể lại một kỷ niệm trước khi đi sâu",
        "Ví dụ: Khi gặp bạn học cũ, bạn có thể hỏi về buổi ngoại khóa thay vì nhắc chuyện riêng.",
    ),
    "cups-7": (
        "nhiều ý muốn nói cần được chọn để người nghe hiểu yêu cầu chính",
        "nêu hàng loạt khả năng rồi mong người kia tự chọn đúng điều mình muốn",
        "chọn một câu hỏi quan trọng nhất cho lần trao đổi này",
        "Ví dụ: Bạn vừa muốn hỏi lịch gặp, vừa hỏi lý do ít nhắn, vừa kể chuyện cũ trong một tin.",
    ),
    "cups-8": (
        "có thể rời một cuộc trao đổi không còn giúp hiểu nhau",
        "dừng bằng lời hờn dỗi để buộc người khác giữ mình lại",
        "báo rõ bạn muốn dừng cuộc trao đổi hiện tại, không đặt điều kiện trừng phạt",
        "Ví dụ: Câu chuyện cứ quay lại lời chê và bạn có thể nói mình không muốn tiếp tục lúc này.",
    ),
    "cups-9": (
        "nói rõ điều mình thích giúp người khác hiểu mà không phải đoán",
        "giấu mong muốn rồi thất vọng vì không ai làm đúng ý",
        "nói một sở thích hoặc mong muốn của bạn như một đề nghị",
        "Ví dụ: Bạn muốn sinh nhật yên tĩnh nhưng chưa nói nên mọi người đang tính tổ chức đông.",
    ),
    "cups-10": (
        "cảm giác thuộc về được nuôi bằng những lời hỏi han cho phép trả lời thật",
        "đòi mọi người tỏ ra vui để giữ không khí hòa thuận",
        "hỏi một câu có chỗ cho cả điều vui lẫn điều chưa ổn",
        "Ví dụ: Trong bữa cơm, bạn muốn nghe mọi người đang cần gì chứ không chỉ hỏi hôm nay "
        "vui không.",
    ),
    "cups-page": (
        "một lời quan tâm đơn giản có thể được nói mà không cần thật khéo",
        "sửa câu mãi vì sợ một lời thật thà trông vụng về",
        "gửi một câu cảm ơn hoặc hỏi han đúng điều bạn muốn nói",
        "Ví dụ: Bạn muốn cảm ơn người đã nghe mình kể nhưng đang tìm lời quá cầu kỳ.",
    ),
    "cups-knight": (
        "lời mời chân thành cần vừa đẹp vừa đúng khả năng giữ lời",
        "hứa lúc xúc động rồi để người nghe chờ điều mình không làm được",
        "nói lời mời cho một việc bạn thật sự có thể sắp xếp",
        "Ví dụ: Lúc muốn rủ đi ăn, bạn chỉ có một buổi tối trống để đưa lời hẹn thật.",
    ),
    "cups-queen": (
        "lắng nghe cảm xúc cần chỗ cho người kể tự gọi tên điều họ trải qua",
        "đoán cảm xúc rồi nói hộ người đang kể",
        "hỏi họ muốn được nghe hay muốn cùng tìm cách giải quyết",
        "Ví dụ: Người thân kể một chuyện buồn, bạn có thể hỏi thay vì nói ngay họ nên làm gì.",
    ),
    "cups-king": (
        "nói rõ cảm xúc mà giữ bình tĩnh giúp người nghe hiểu bạn",
        "giấu điều buồn sau câu mình ổn để tránh một cuộc trao đổi khó",
        "nói bạn cảm thấy thế nào và cần gì, không gán lỗi cho người nghe",
        "Ví dụ: Khi một cuộc gọi bị quên, bạn có thể kể cảm giác buồn của mình mà không buộc tội.",
    ),
    "swords-ace": (
        "một câu nói chính xác có thể tháo hiểu lầm đang kéo dài",
        "nói thẳng bằng lời tuyệt đối khiến người nghe phải tự bảo vệ",
        "nêu đúng sự việc và câu hỏi bạn muốn được trả lời",
        "Ví dụ: Bạn muốn biết lịch có đổi không và có thể hỏi đúng ngày thay vì nói sao lúc "
        "nào cũng đổi.",
    ),
    "swords-2": (
        "chưa có câu trả lời vẫn có thể nói rõ mình đang cân nhắc gì",
        "né trả lời để khỏi mất lòng rồi để người khác chờ vô hạn",
        "nói phần chưa quyết được và lúc bạn có thể trả lời",
        "Ví dụ: Khi chưa biết có đi cùng không, bạn có thể báo thời hạn xác nhận của mình.",
    ),
    "swords-3": (
        "lời làm mình buồn cần được nhắc đúng câu và đúng tác động",
        "đáp lại bằng lời đau hơn để người kia hiểu mình bị tổn thương",
        "nói câu nào khiến bạn buồn và đề nghị không dùng cách nói ấy nữa",
        "Ví dụ: Bạn không thích một câu đùa về mình trước nhóm và muốn nói riêng với người đã "
        "trêu.",
    ),
    "swords-4": (
        "tạm nghỉ nói chuyện giúp tránh tiếp tục khi đã khó lắng nghe",
        "im lặng để người kia lo thay vì báo mình cần nghỉ",
        "xin nghỉ và hẹn thời điểm có thể quay lại nếu bạn muốn tiếp tục",
        "Ví dụ: Khi cuộc gọi kéo dài và đã mệt, bạn muốn hẹn nói tiếp sau bữa tối.",
    ),
    "swords-5": (
        "cần xem lời đáp đang giải quyết vấn đề hay chỉ giành phần thắng",
        "giữ lời cuối bằng một câu hạ thấp người đang nói",
        "bỏ câu công kích và hỏi điều nào còn cần thống nhất",
        "Ví dụ: Bạn tìm được điểm sai trong lời người kia nhưng điều cần bàn là cách chia việc "
        "nhà.",
    ),
    "swords-6": (
        "đổi cách trao đổi có thể giúp hai bên rời một vòng tranh cãi",
        "đổi chủ đề để né điều vẫn cần được làm rõ",
        "chọn một kênh hoặc thời điểm khác rồi giữ đúng vấn đề cần bàn",
        "Ví dụ: Tin nhắn khiến câu nào cũng bị hiểu gắt nên hai người hẹn một cuộc gọi ngắn.",
    ),
    "swords-7": (
        "sự riêng tư và thông tin người khác cần biết phải được phân biệt",
        "nói tránh khiến người nghe hiểu sai phần liên quan đến họ",
        "nói phần cần thiết và báo rõ phần riêng bạn chưa muốn chia sẻ",
        "Ví dụ: Bạn muốn giữ lý do riêng nhưng vẫn cần báo người đang chờ rằng mình không thể đến.",
    ),
    "swords-8": (
        "sợ phản ứng có thể làm bạn quên rằng mình được quyền không trả lời",
        "tự buộc phải giải thích mọi chuyện dù không thấy thoải mái",
        "chuẩn bị một câu từ chối chia sẻ phần riêng tư",
        "Ví dụ: Có người hỏi chuyện cá nhân trong nhóm và bạn có thể nói mình không muốn kể.",
    ),
    "swords-9": (
        "nghĩ đi nghĩ lại một câu chưa chắc giúp hiểu đúng người nói",
        "đọc lại tin nhắn để tìm bằng chứng cho điều mình sợ",
        "ghi một câu cần hỏi lại rồi ngừng dò từng chữ",
        "Ví dụ: Bạn đã đọc một lời trả lời cả chục lần nhưng vẫn chưa biết người gửi muốn hẹn "
        "ngày nào.",
    ),
    "swords-10": (
        "một cuộc trao đổi đã quá sức có thể dừng mà chưa có lời giải thích trọn vẹn",
        "cố nói tiếp để nhận được câu trả lời cuối cùng bằng mọi giá",
        "dừng cuộc trò chuyện đang làm bạn quá mệt và tìm người tin cậy nếu cần",
        "Ví dụ: Khi hai bên lặp lời trách suốt cuộc gọi, bạn muốn kết thúc cuộc gọi đó.",
    ),
    "swords-page": (
        "hỏi có mục đích giúp phân biệt điều đã biết và điều cần xác nhận",
        "hỏi dồn như kiểm tra khiến người nghe khó trả lời thật",
        "đặt một câu hỏi mở về chi tiết chưa rõ rồi chờ",
        "Ví dụ: Lúc nghe hai phiên bản của một lời hẹn, bạn cần hỏi ngày nào đã được xác nhận.",
    ),
    "swords-knight": (
        "ý kiến sắc cần được nói sau khi đã nghe đủ câu của người khác",
        "phản bác ngay từ vài chữ đầu nên đáp nhầm ý",
        "để người kia nói hết rồi nhắc đúng điểm bạn muốn phản hồi",
        "Ví dụ: Bạn định cắt lời khi nghe một đề nghị nhưng phần sau có thể chứa điều kiện "
        "quan trọng.",
    ),
    "swords-queen": (
        "giới hạn có thể nói thẳng mà không cần chê con người của ai",
        "giải thích quá dài khiến lời từ chối nghe như còn có thể thương lượng",
        "nói rõ điều bạn không đồng ý bằng một câu về mình",
        "Ví dụ: Khi bị hỏi mượn tài khoản, bạn muốn từ chối rõ thay vì tìm nhiều lý do.",
    ),
    "swords-king": (
        "lý lẽ rõ giúp thỏa thuận nếu vẫn ghi nhận điều người nghe đang quan tâm",
        "đòi người khác bỏ cảm xúc để chứng minh mình hợp lý hơn",
        "nói lại điều bạn đã nghe rồi nêu tiêu chí cho đề nghị của mình",
        "Ví dụ: Hai người chọn nơi ở cần nói cả quãng đường đi lẫn cảm giác thoải mái của mỗi bên.",
    ),
    "pentacles-ace": (
        "lời nói có thể thành một cuộc hẹn rõ thời gian và địa điểm",
        "nói khi nào rảnh gặp mà không đưa cách chốt cụ thể",
        "chọn một thời điểm có thật trong lịch để đề nghị gặp",
        "Ví dụ: Khi muốn gặp bạn cũ, bạn đưa hai buổi mình có thể đi thay vì hẹn chung chung.",
    ),
    "pentacles-2": (
        "nhiều cuộc trao đổi cần được sắp xếp để bạn trả lời có chú ý",
        "nhận mọi cuộc gọi ngay rồi không nghe rõ cuộc nào",
        "nói rõ thời gian trả lời cho một cuộc trao đổi đang chờ",
        "Ví dụ: Bạn đang nói với người thân nhưng liên tục trả lời nhóm chat nên bỏ sót câu hỏi.",
    ),
    "pentacles-3": (
        "phối hợp cần lời xác nhận về từng phần chứ không chỉ đồng ý chung",
        "nghĩ ai cũng tự hiểu mình cần chuẩn bị gì",
        "nhắc phần của từng người và hỏi có cần sửa điều gì không",
        "Ví dụ: Nhóm đã chốt ngày ăn cùng nhau nhưng chưa ai nói việc mình sẽ chuẩn bị món gì.",
    ),
    "pentacles-4": (
        "giữ riêng chuyện cá nhân cần ranh giới được nói rõ",
        "giữ kín cả điều liên quan đến người khác rồi để họ phải đoán",
        "nói bạn có thể chia sẻ đến đâu mà không ép mình kể thêm",
        "Ví dụ: Bạn muốn báo một thay đổi trong lịch nhưng không muốn kể chi tiết gia đình.",
    ),
    "pentacles-5": (
        "cảm giác bị bỏ ngoài có thể được nói bằng một nhu cầu cụ thể",
        "không hỏi rồi kết luận mình không được chào đón",
        "hỏi bạn có thể tham gia phần nào nếu thật sự muốn tham gia",
        "Ví dụ: Bạn thấy nhóm bàn một buổi đi chơi nhưng chưa biết có lời mời mở cho mọi người "
        "không.",
    ),
    "pentacles-6": (
        "lắng nghe và được lắng nghe cần có chỗ cho hai phía",
        "cho nhiều lời khuyên mà chưa hỏi người kia muốn nói điều gì",
        "nói bạn muốn được nghe hết rồi dành lượt tương tự cho người kia",
        "Ví dụ: Một người kể rất lâu, còn bạn cũng có chuyện muốn kể và cần xin một lượt nói.",
    ),
    "pentacles-7": (
        "cần cho một thỏa thuận thời gian để xem cách trao đổi có thay đổi không",
        "đòi thấy khác ngay sau một lần nói chuyện",
        "đặt một lần hẹn xem điều đã thống nhất có thuận tiện không",
        "Ví dụ: Hai người vừa đổi cách báo khi trễ hẹn và có thể xem lại sau vài lần gặp.",
    ),
    "pentacles-8": (
        "giao tiếp rõ hơn đến từ việc tập sửa một thói quen nhỏ",
        "cố nói hoàn hảo đến mức không còn nghe người đối diện",
        "thử nhắc lại ý người nghe trước khi đưa câu trả lời",
        "Ví dụ: Khi gọi điện hôm nay, bạn muốn thử nghe hết câu thay vì đáp ngay như thường lệ.",
    ),
    "pentacles-9": (
        "tự chủ giúp bạn chọn lúc và mức độ liên lạc phù hợp",
        "tỏ ra không cần ai nên không nói lúc mình muốn được trò chuyện",
        "nói rõ một lúc bạn muốn kết nối và một lúc cần riêng tư",
        "Ví dụ: Bạn thích buổi tối riêng nhưng vẫn muốn có lịch gọi cho bạn vào cuối tuần.",
    ),
    "pentacles-10": (
        "chuyện có nhiều người liên quan cần tiếng nói của người chịu ảnh hưởng",
        "dùng lệ gia đình để chốt thay người chưa được hỏi",
        "hỏi từng người liên quan điều họ cần trước khi thống nhất",
        "Ví dụ: Gia đình chọn ngày họp mặt và cần hỏi cả người phải đi xa.",
    ),
    "pentacles-page": (
        "học cách hỏi rõ bắt đầu bằng một câu cụ thể và chịu sửa khi hiểu sai",
        "giả vờ hiểu vì ngại hỏi một điều cơ bản",
        "hỏi lại nghĩa của một chi tiết bạn chưa hiểu",
        "Ví dụ: Bạn chưa biết nơi hẹn ở cổng nào và có thể hỏi trước khi lên đường.",
    ),
    "pentacles-knight": (
        "sự đáng tin trong giao tiếp được tạo bằng việc giữ lời đã nói",
        "trả lời theo thói quen mà không đọc câu hỏi lần này",
        "kiểm tra lời hẹn đang có và báo sớm nếu không thể giữ",
        "Ví dụ: Khi bị trùng lịch, bạn cần báo sớm về cuộc gọi mình đã hứa vào tối nay.",
    ),
    "pentacles-queen": (
        "quan tâm thiết thực bắt đầu từ hỏi điều người nghe thật sự cần",
        "đưa giải pháp ngay rồi làm người kể thấy chưa được nghe",
        "hỏi một việc cụ thể bạn có thể giúp mà không quyết định hộ",
        "Ví dụ: Người thân nói đang bận, bạn hỏi họ muốn được giúp mua đồ hay chỉ muốn kể.",
    ),
    "pentacles-king": (
        "lời cam kết cần mức thực hiện rõ để người nghe biết có thể trông cậy gì",
        "hứa giúp không giới hạn rồi dùng lời hứa để có quyền quyết định",
        "nói rõ phần có thể giữ lời mà không kèm yêu cầu kiểm soát",
        "Ví dụ: Bạn nhận giúp một buổi chuyển nhà và cần nói với người nhờ rằng mình chỉ đến "
        "được buổi sáng.",
    ),
}

_ENERGY: dict[str, _Entry] = {
    "major-fool": (
        "đổi một hoạt động quen có thể giúp bạn thấy muốn bắt đầu hơn",
        "lấp lịch bằng trải nghiệm mới để tránh nhìn mức sức hiện tại",
        "thử một việc mới trong thời gian ngắn rồi xem bạn còn muốn tiếp tục không",
        "Ví dụ: Bạn muốn ra ngoài sau buổi làm việc nhưng có thể chỉ đi một vòng gần nhà.",
    ),
    "major-magician": (
        "tận dụng điều đã biết giúp giảm công sức khởi động",
        "tìm cách làm hoàn toàn mới cho việc mình đã có công cụ xử lý",
        "chọn công cụ quen để hoàn thành một việc đang ngại bắt đầu",
        "Ví dụ: Bạn có sẵn danh sách đồ cần mua nhưng lại lập thêm ứng dụng lúc đã mệt.",
    ),
    "major-high-priestess": (
        "chú ý cảm giác hiện tại giúp biết khi nào mình cần ít kích thích hơn",
        "tự gán nguyên nhân cho sự mệt mà chưa xem hôm nay đã làm gì",
        "viết lúc bạn thấy khó tập trung và hoạt động ngay trước đó",
        "Ví dụ: Sau cuộc gọi có nhiều người tham gia, bạn muốn ngồi yên thay vì mở thêm chương "
        "trình có tiếng.",
    ),
    "major-empress": (
        "điều kiện dễ chịu giúp bạn không phải gắng thêm cho những việc cơ bản",
        "lo không gian đẹp mà quên điều mình thật sự cần để thoải mái",
        "chọn một thay đổi nhỏ khiến chỗ bạn đang ngồi dễ chịu hơn",
        "Ví dụ: Bạn đang làm việc ở bàn chật và có thể dọn chỗ đặt tay trước khi làm tiếp.",
    ),
    "major-emperor": (
        "một lịch đơn giản giúp tiết kiệm sức quyết định việc tiếp theo",
        "ép mình theo lịch cứng dù hôm nay có ít sức hơn",
        "đặt hai việc chính và chừa khoảng trống giữa chúng",
        "Ví dụ: Lịch cuối tuần kín từ sáng đến tối khiến bạn không có lúc ngồi nghỉ.",
    ),
    "major-hierophant": (
        "thói quen có ích giúp bạn đỡ phải nghĩ lại cách làm mỗi ngày",
        "giữ một lệ sinh hoạt chỉ vì người khác bảo phải làm thế",
        "giữ một thói quen thật sự giúp bạn và bỏ yêu cầu không phù hợp",
        "Ví dụ: Bạn chuẩn bị đồ từ tối thấy tiện, nhưng lịch dậy sớm của người khác không hợp "
        "mình.",
    ),
    "major-lovers": (
        "sức có hạn cần được dành cho hoạt động phù hợp điều bạn muốn",
        "nhận lời theo mong đợi của mọi người rồi không còn sức cho mình",
        "chọn một hoạt động đáng giữ và từ chối một lịch không cần thiết",
        "Ví dụ: Khi có một buổi trống, bạn cân nhắc gặp bạn thân hay dự thêm một cuộc tụ tập.",
    ),
    "major-chariot": (
        "tập trung vào một đích nhỏ giúp công sức không bị chia quá nhiều",
        "dùng quyết tâm để ép mình chạy hết một danh sách dài",
        "chọn một việc cần xong và dừng ở mốc đã đặt",
        "Ví dụ: Bạn muốn dọn cả nhà nhưng có thể hoàn thành góc bàn trước khi nghỉ.",
    ),
    "major-strength": (
        "điều chỉnh sức bỏ ra cũng là cách giữ được điều bạn muốn làm",
        "coi nghỉ hoặc làm ít hơn là biểu hiện yếu kém",
        "chọn mức dễ hơn cho một việc thay vì cố bằng mức hôm nhiều sức",
        "Ví dụ: Bạn thích đi bộ nhưng hôm nay có thể chọn đường ngắn hơn khi đã mệt.",
    ),
    "major-hermit": (
        "thời gian yên tĩnh có thể giúp bạn gom lại sự chú ý",
        "ở riêng nhưng vẫn lướt liên tục nên không thật sự bớt tiếng ồn",
        "đặt điện thoại xuống một lúc và chọn hoạt động yên tĩnh bạn thích",
        "Ví dụ: Bạn muốn nghỉ sau khi gặp nhiều người nhưng màn hình vẫn liên tục kéo bạn đọc tin.",
    ),
    "major-wheel-of-fortune": (
        "sức và độ tập trung có thể khác nhau giữa các ngày",
        "đòi hôm nay phải làm được bằng hôm trước dù lịch đã khác",
        "chọn thứ tự việc theo mức sức bạn nhận thấy lúc này",
        "Ví dụ: Bạn có nhiều cuộc gọi hơn thường lệ nên việc cần tập trung có thể phải để sau.",
    ),
    "major-justice": (
        "nhìn lượng việc thực tế giúp đánh giá công sức công bằng với mình",
        "so kết quả của mình với người có lịch và hỗ trợ khác",
        "viết những việc đã làm hôm nay trước khi nhận thêm",
        "Ví dụ: Bạn nghĩ mình làm ít nhưng đã dành cả buổi giúp người nhà xử lý giấy tờ.",
    ),
    "major-hanged-man": (
        "tạm dừng một cách làm tốn sức có thể giúp tìm cách nhẹ hơn",
        "cố thêm cùng một thao tác dù càng làm càng khó tập trung",
        "rời việc đang mắc một lúc rồi thử cách đơn giản hơn",
        "Ví dụ: Khi xếp đồ mãi không vừa, bạn có thể dừng để chọn bớt thứ cần giữ.",
    ),
    "major-death": (
        "bỏ một hoạt động không còn cần thiết giúp giảm phần sức bị hao",
        "giữ mọi thói quen của giai đoạn cũ dù lịch đã thay đổi",
        "chọn một việc không còn cần làm và gỡ nó khỏi lịch",
        "Ví dụ: Bạn vẫn dự cuộc họp của nhóm cũ dù đã bàn giao xong việc liên quan.",
    ),
    "major-temperance": (
        "xen việc cần chú ý với khoảng nghỉ giúp mức cố gắng vừa sức hơn",
        "dồn hết việc vào một lượt rồi mất cả buổi để lấy lại sức",
        "đặt một khoảng nghỉ giữa hai hoạt động tốn nhiều chú ý",
        "Ví dụ: Bạn có thể chừa thời gian yên tĩnh sau cuộc họp trước khi đi gặp nhóm bạn.",
    ),
    "major-devil": (
        "một thói quen dễ cuốn vào có thể đang chiếm phần chú ý bạn muốn giữ",
        "mở màn hình theo tay quen dù đã định nghỉ",
        "ẩn một thông báo thường kéo bạn quay lại khi muốn dừng",
        "Ví dụ: Bạn mở video để nghỉ vài phút nhưng cứ xem tiếp mỗi lần có đề xuất mới.",
    ),
    "major-tower": (
        "lịch bị xáo trộn cần được thu gọn trước khi cố làm đủ mọi thứ",
        "thêm việc phát sinh mà giữ nguyên mọi cam kết cũ",
        "chọn việc thật sự cần trong ngày và dời phần còn lại",
        "Ví dụ: Một chuyến xe bị trễ khiến bạn không còn đủ thời gian cho ba việc đã hẹn.",
    ),
    "major-star": (
        "một hoạt động nhẹ bạn còn thích có thể giúp tìm lại hứng thú",
        "đòi mình phải thấy khá hơn ngay sau một khoảng nghỉ",
        "thử một việc dễ chịu không cần đạt kết quả",
        "Ví dụ: Sau tuần nhiều việc phải làm, bạn muốn nghe một bài hát quen mà không cần làm "
        "thêm gì.",
    ),
    "major-moon": (
        "khi khó biết mình mệt vì đâu, có thể bắt đầu từ lịch sinh hoạt đã thấy",
        "đoán nguyên nhân xa xôi cho cảm giác hiện tại",
        "ghi điều đã làm và chọn giảm một nguồn gây phân tâm rõ nhất",
        "Ví dụ: Bạn thấy khó tập trung sau nhiều tin nhắn nhưng chưa cần kết luận nguyên nhân "
        "sâu xa.",
    ),
    "major-sun": (
        "niềm vui rõ ràng giúp bạn nhận ra hoạt động nào mình muốn dành sức",
        "vui nên nhận thêm đến mức không còn khoảng nghỉ",
        "giữ một hoạt động bạn thích và chừa thời gian dừng sau đó",
        "Ví dụ: Bạn rất vui ở buổi gặp nhưng vẫn có thể về đúng lúc đã định.",
    ),
    "major-judgement": (
        "nhìn lại những ngày quá sức giúp bạn đổi cách dùng thời gian",
        "tự trách vì mệt thay vì xem phần lịch có thể sửa",
        "chọn một điều từng làm bạn quá tải để thay đổi lần tới",
        "Ví dụ: Lần nào nhận hai buổi hẹn liền nhau bạn cũng mệt và muốn chừa khoảng cách.",
    ),
    "major-world": (
        "việc đã hoàn thành cần một điểm dừng để bạn không tiếp tục bỏ sức",
        "tìm thêm việc ngay vì chưa quen cảm giác đã xong",
        "viết dấu hoàn tất cạnh việc đã xong rồi nghỉ trước việc mới",
        "Ví dụ: Khi đã chuẩn bị đủ đồ cho chuyến đi, bạn vẫn kiểm lại túi nhiều lần.",
    ),
    "wands-ace": (
        "hứng thú ban đầu có thể được dùng cho một lượt thử ngắn",
        "tiêu hết sức ở buổi đầu vì muốn làm ngay mọi ý tưởng",
        "thử phần khiến bạn háo hức nhất và đặt giờ dừng",
        "Ví dụ: Bạn muốn tập một điệu nhảy mới và có thể thử một đoạn lúc còn thấy vui.",
    ),
    "wands-2": (
        "lập một lựa chọn rõ giúp đỡ tốn sức cân nhắc cả ngày",
        "nghĩ hết mọi hoạt động có thể làm mà không chọn việc nào",
        "chọn trước một việc cho khoảng thời gian trống tiếp theo",
        "Ví dụ: Lúc phân vân ở nhà hay ra ngoài, bạn mất cả giờ rồi không còn muốn làm gì.",
    ),
    "wands-3": (
        "việc đã bắt đầu cần thời gian tiến triển mà không phải luôn thúc thêm",
        "kiểm kết quả liên tục khiến sự chú ý bị giữ ở một chỗ",
        "đặt một lúc xem lại rồi chuyển sang việc nhẹ khác",
        "Ví dụ: Bạn đã gửi lời đăng ký và cứ kiểm hộp thư mỗi lần cầm điện thoại.",
    ),
    "wands-4": (
        "dừng ở một mốc vui giúp bạn thấy công sức đã có điểm đến",
        "vừa xong đã thêm mục tiêu khiến niềm vui không có chỗ",
        "viết một việc đã xong và dành một khoảng nghỉ bạn thích",
        "Ví dụ: Khi đã dọn xong phòng, bạn có thể đọc vài trang thay vì dọn thêm tủ.",
    ),
    "wands-5": (
        "nhiều yêu cầu cùng kéo chú ý cần được tách ra để đỡ hao sức",
        "đáp ứng mọi tiếng gọi ngay khiến việc nào cũng bị ngắt",
        "chọn một việc và tắt bớt nguồn ngắt quãng trong lúc làm",
        "Ví dụ: Khi vừa nấu ăn, đọc tin vừa nghe cuộc gọi, bạn liên tục quên bước đang làm.",
    ),
    "wands-6": (
        "nhận ra điều làm được giúp bạn không chỉ nhìn phần còn thiếu",
        "cố hơn chỉ để giữ mức được khen của lần trước",
        "ghi một tiến bộ có thật rồi chọn mức làm vừa sức hôm nay",
        "Ví dụ: Lần trước bạn hoàn thành nhiều việc, nhưng hôm nay không cần lặp đúng số lượng ấy.",
    ),
    "wands-7": (
        "bảo vệ thời gian riêng giúp phần sức còn lại không bị chia hết",
        "giải thích mọi lời từ chối đến mức mất thêm cả buổi",
        "nói một giới hạn ngắn về việc bạn không nhận hôm nay",
        "Ví dụ: Bạn đã dành tối để nghỉ nhưng vẫn có người nhờ thêm một việc không gấp.",
    ),
    "wands-8": (
        "nhiều việc đến nhanh cần được lọc trước khi bạn cuốn theo",
        "nhầm tốc độ xử lý với khả năng làm thêm không giới hạn",
        "chọn yêu cầu cần trả lời ngay và để phần khác vào một lượt sau",
        "Ví dụ: Điện thoại báo tin liên tục lúc bạn đang chuẩn bị bữa ăn.",
    ),
    "wands-9": (
        "sức đã dùng nhiều cần được tính đến ở chặng còn lại",
        "cố thêm để chứng minh mình chưa mệt",
        "chọn phần cần giữ và giảm một việc có thể để sau",
        "Ví dụ: Bạn đã chạy việc cả ngày và có thể để việc xếp lại kệ sang hôm khác.",
    ),
    "wands-10": (
        "gánh quá nhiều phần cùng lúc cần được đặt bớt xuống",
        "tự làm mọi việc vì nghĩ nhờ người khác sẽ phiền hơn",
        "nhờ một người nhận một việc cụ thể hoặc bỏ bớt việc chưa cần",
        "Ví dụ: Bạn vừa mua đồ vừa nấu vừa dọn cho buổi gặp trong khi những người khác có thể "
        "giúp.",
    ),
    "wands-page": (
        "sự tò mò nhẹ có thể giúp bạn thử lại một hoạt động đang bỏ quên",
        "biến sở thích mới thành lịch phải hoàn thành mỗi ngày",
        "thử một hoạt động chỉ để biết mình có thích không",
        "Ví dụ: Bạn muốn thử vẽ lúc rảnh và chưa cần đặt mục tiêu phải vẽ đẹp.",
    ),
    "wands-knight": (
        "một lúc nhiều hứng cần điểm dừng để bạn không nhận quá sức",
        "xếp kín cả tuần khi đang thấy mình làm được mọi thứ",
        "giữ một buổi trống trước khi nhận hoạt động tiếp theo",
        "Ví dụ: Bạn hứng thú đăng ký nhiều lớp nhưng lịch di chuyển giữa các nơi chưa được tính.",
    ),
    "wands-queen": (
        "hoạt động mình thích có thể tiếp sức mà không cần biểu diễn cho ai",
        "giữ vai người sôi nổi dù lúc này muốn yên tĩnh",
        "chọn cách tham gia đúng mức hứng thú hiện tại của bạn",
        "Ví dụ: Bạn thường khuấy động buổi gặp nhưng lần này muốn ngồi nghe nhiều hơn.",
    ),
    "wands-king": (
        "dành sức cho hướng chính cần biết phần nào không phải tự mình làm",
        "cầm mọi việc để giữ kiểm soát rồi không còn chú ý cho việc quan trọng",
        "chọn việc cần bạn trực tiếp làm và chia phần khác nếu có người nhận",
        "Ví dụ: Bạn tổ chức chuyến đi nhưng không cần tự kiểm đồ của từng người đi cùng.",
    ),
    "cups-ace": (
        "cảm giác dễ chịu mới là điều đáng để ý khi chọn hoạt động trong ngày",
        "coi một lần vui là yêu cầu phải luôn thấy vui với hoạt động đó",
        "ghi một khoảnh khắc bạn thấy nhẹ hơn và điều đang làm lúc ấy",
        "Ví dụ: Bạn thấy dễ chịu khi nghe nhạc lúc rửa bát và muốn nhớ điều nhỏ đó.",
    ),
    "cups-2": (
        "một cuộc gặp có sự đáp lại có thể dễ chịu hơn việc cố giữ chuyện một mình",
        "tiếp tục kết nối khi đã hết sức chỉ vì người kia còn muốn nói",
        "chọn độ dài cuộc gặp phù hợp và báo lúc bạn cần dừng",
        "Ví dụ: Bạn thích trò chuyện với một người nhưng tối nay chỉ có sức gọi khoảng mười phút.",
    ),
    "cups-3": (
        "gặp nhóm phù hợp có thể đem lại niềm vui mà không phải luôn cố hòa nhập",
        "tham gia mọi cuộc vui dù đã muốn về nghỉ",
        "chọn một buổi gặp bạn thật sự muốn và bỏ bớt lịch còn lại",
        "Ví dụ: Khi được rủ ba buổi trong tuần, bạn chỉ muốn dành sức cho một nhóm thân.",
    ),
    "cups-4": (
        "thiếu hứng có thể là lúc bạn không muốn nhận thêm kích thích",
        "ép mình chọn ngay một hoạt động để chứng minh không lười",
        "đặt các lời mời sang một bên và nghỉ trước khi chọn",
        "Ví dụ: Bạn xem nhiều lựa chọn giải trí sau khi làm việc nhưng không muốn bắt đầu cái nào.",
    ),
    "cups-5": (
        "thất vọng có thể chiếm nhiều chú ý hơn bạn nhận ra",
        "bắt mình làm đủ như thường lệ khi vẫn đang buồn về một việc",
        "chọn việc thiết yếu và để một khoảng không phải xử lý gì thêm",
        "Ví dụ: Một kế hoạch bị hủy làm bạn hụt hẫng và việc thường ngày hôm nay cũng thấy khó "
        "hơn.",
    ),
    "cups-6": (
        "hoạt động quen có thể giúp bạn bớt tốn sức thích nghi",
        "so sự vui hiện tại với ký ức đẹp rồi thấy gì cũng kém",
        "chọn một điều quen dễ chịu mà không đòi cảm giác phải giống ngày xưa",
        "Ví dụ: Bạn muốn nghe lại bài nhạc cũ khi đi xe nhưng không cần vui như lần đầu nghe.",
    ),
    "cups-7": (
        "quá nhiều lựa chọn nghỉ ngơi cũng có thể làm bạn thêm mệt",
        "tìm hoạt động hoàn hảo rồi không dành được thời gian nghỉ thật",
        "chọn một việc nghỉ đơn giản đã biết mình thấy dễ chịu",
        "Ví dụ: Bạn lướt danh sách phim cả tối trong khi chỉ muốn có một lúc thư giãn.",
    ),
    "cups-8": (
        "hoạt động từng vui có thể không còn đáng dành sức lúc này",
        "tiếp tục tham gia chỉ vì đã có mặt từ trước",
        "giảm một hoạt động không còn muốn làm và xem khoảng trống ấy có ích không",
        "Ví dụ: Bạn vẫn vào nhóm trò chuyện mỗi tối dù lần nào xong cũng thấy mình mệt hơn.",
    ),
    "cups-9": (
        "biết điều đủ vui giúp bạn dừng tìm thêm mà chưa thấy hài lòng",
        "kéo dài hoạt động thú vị đến mức bỏ qua giờ đã muốn nghỉ",
        "chọn điểm dừng để giữ cảm giác dễ chịu của việc đang làm",
        "Ví dụ: Bạn thích xem phim nhưng có thể dừng sau một tập lúc đã thấy đủ.",
    ),
    "cups-10": (
        "ở nơi được là mình có thể bớt phần sức phải cố tỏ ra ổn",
        "gánh việc giữ không khí vui cho cả nhà hoặc cả nhóm",
        "nói mức tham gia bạn thấy thoải mái và để người khác cùng góp phần",
        "Ví dụ: Trong buổi họp mặt, bạn không cần kể chuyện liên tục để mọi người có chuyện vui.",
    ),
    "cups-page": (
        "một niềm vui nhỏ có thể được đón nhận mà không cần biến thành mục tiêu",
        "vừa thích điều gì đã tự đặt yêu cầu phải làm thật tốt",
        "thử một việc dễ thương bạn thích mà không chấm kết quả",
        "Ví dụ: Bạn muốn gấp một con vật bằng giấy lúc nghỉ và không cần làm thật đẹp.",
    ),
    "cups-knight": (
        "cảm hứng dễ chịu cần một hoạt động vừa với sức thực tế",
        "lập buổi đi chơi cầu kỳ chỉ vì đang rất háo hức",
        "chọn phiên bản đơn giản của hoạt động khiến bạn muốn tham gia",
        "Ví dụ: Khi muốn có buổi tối đặc biệt, bạn thấy một cuộc đi dạo gần nhà đã đủ.",
    ),
    "cups-queen": (
        "nghe chuyện của người khác cũng cần tính đến mức chú ý mình còn có",
        "nhận nghe mọi chuyện rồi không còn khoảng riêng để nghỉ",
        "nói thời gian bạn có thể lắng nghe và giữ một khoảng cho mình",
        "Ví dụ: Nhiều người gọi kể chuyện trong ngày khiến buổi tối riêng của bạn bị chia hết.",
    ),
    "cups-king": (
        "giữ bình tĩnh không có nghĩa phải nhận hết phần căng thẳng của mọi người",
        "đóng vai người luôn ổn rồi bỏ qua lúc mình cần dừng",
        "nói khi bạn không còn đủ sức tiếp tục một cuộc trao đổi",
        "Ví dụ: Bạn đang giúp hai người hòa giải nhưng đã mệt và cần kết thúc cuộc gọi.",
    ),
    "swords-ace": (
        "gọi đúng việc cần làm giúp giảm phần sức dùng để nghĩ vòng quanh",
        "phân tích rộng hơn mức cần cho một quyết định nhỏ",
        "viết câu hỏi chính và chỉ tìm thông tin giúp trả lời câu ấy",
        "Ví dụ: Khi chọn giờ đi chợ, bạn lại đọc cả loạt mẹo sắp xếp sinh hoạt.",
    ),
    "swords-2": (
        "một lựa chọn đang treo có thể chiếm chú ý dù bạn chưa làm gì",
        "giữ cả hai phương án mở chỉ để tránh cảm giác chọn sai",
        "chọn theo một tiêu chí đơn giản nếu quyết định còn có thể đổi",
        "Ví dụ: Bạn mất nhiều giờ chọn giờ gặp trong khi cả hai buổi đều có thể đổi lại.",
    ),
    "swords-3": (
        "một chuyện buồn cần chỗ trong ngày thay vì phải giấu khi làm mọi việc",
        "ép mình giữ lịch kín để khỏi cảm thấy điều khó chịu",
        "giảm một việc không gấp và chọn người bạn muốn kể nếu cần",
        "Ví dụ: Sau một lời làm mình buồn, bạn muốn có buổi tối ít việc hơn thường lệ.",
    ),
    "swords-4": (
        "đầu óc đã làm việc nhiều cần khoảng không phải nhận thêm thông tin",
        "gọi việc lướt tin liên tục là nghỉ dù vẫn thấy mệt",
        "rời màn hình một lúc và chọn cách nghỉ không cần đọc thêm",
        "Ví dụ: Bạn đã đọc tài liệu cả ngày nhưng lúc nghỉ vẫn mở các bài hướng dẫn mới.",
    ),
    "swords-5": (
        "tranh luận để hơn thua có thể tiêu sức mà không giải quyết điều gì",
        "quay lại cuộc cãi nhau chỉ để tìm câu đáp hay hơn",
        "dừng soạn lời phản bác và chọn việc khác đang cần chú ý",
        "Ví dụ: Sau lần tranh luận trên mạng, bạn dành cả tối nghĩ câu đáp dù câu chuyện không "
        "còn hữu ích.",
    ),
    "swords-6": (
        "chuyển sang môi trường ít ngắt quãng có thể giảm phần sức phải chống nhiễu",
        "đổi chỗ nhưng mang theo mọi nguồn gây phân tâm",
        "chọn một nơi yên hơn và để bớt thiết bị báo tin bên cạnh",
        "Ví dụ: Bạn chuyển chỗ đọc sách nhưng điện thoại vẫn báo tin mỗi lần có người nhắn.",
    ),
    "swords-7": (
        "cách làm ít tốn sức có ích nếu không để lại việc khó cho người khác",
        "né một việc cần nói rồi mất sức nhớ cách tránh nó",
        "nói phần chưa làm được thay vì tiếp tục tìm cách che đi",
        "Ví dụ: Khi chưa trả lời một lời nhờ, bạn cứ tránh mở nhóm chat vì ngại bị hỏi.",
    ),
    "swords-8": (
        "cảm giác không được nghỉ cần được kiểm tra với yêu cầu có thật",
        "tự đặt luật phải xong tất cả mới được dừng",
        "hỏi việc nào thực sự cần hôm nay và cho phép phần khác chờ",
        "Ví dụ: Bạn nghĩ phải dọn hết trước khi ngủ dù chỉ một góc đang cần xử lý.",
    ),
    "swords-9": (
        "suy nghĩ lặp lại có thể giữ chú ý ngay cả khi không có thông tin mới",
        "tiếp tục tìm câu trả lời lúc đầu óc đã mệt",
        "viết điều cần xem lại vào ngày mai rồi dừng tìm thêm tối nay",
        "Ví dụ: Bạn đọc lại một thư vào lúc khuya dù chưa có gì mới để quyết định.",
    ),
    "swords-10": (
        "khi đã hết sức, giảm yêu cầu có thể quan trọng hơn cố hoàn tất",
        "dùng phần sức cuối để chứng minh mình vẫn làm được",
        "chọn việc thiết yếu và nhờ người hỗ trợ phần cần xử lý",
        "Ví dụ: Sau ngày nhiều việc phải làm, bạn không còn muốn chuẩn bị thêm một buổi gặp "
        "tại nhà.",
    ),
    "swords-page": (
        "tò mò cần được giới hạn để bạn không phải đọc mọi thông tin vừa xuất hiện",
        "mở thêm nhiều nguồn khiến câu hỏi ban đầu bị quên",
        "chọn một nguồn để trả lời điều đang tìm rồi đóng phần còn lại",
        "Ví dụ: Bạn tra giờ xe nhưng mỗi lần mở trang lại bị kéo sang một bài khác.",
    ),
    "swords-knight": (
        "tốc độ suy nghĩ cao vẫn cần một việc chính để không chạy theo mọi ý",
        "vừa nghĩ ra đã chuyển việc khiến chú ý bị xé nhỏ",
        "viết ý mới vào danh sách rồi quay lại việc đang chọn",
        "Ví dụ: Bạn đang đọc nhưng cứ đứng lên làm mỗi việc nhỏ vừa nhớ ra.",
    ),
    "swords-queen": (
        "cắt bớt yêu cầu không cần thiết giúp giữ đầu óc rõ cho điều quan trọng",
        "dùng lời gắt để chặn người khác khi mình đã mệt",
        "nói ngắn điều bạn không thể nhận thay vì giải thích trong bực bội",
        "Ví dụ: Khi cần buổi tối yên tĩnh, bạn có thể từ chối một cuộc gọi không gấp.",
    ),
    "swords-king": (
        "quy tắc ưu tiên rõ giúp tiết kiệm sức phải chọn lại từng việc",
        "đặt quá nhiều quy tắc khiến việc đơn giản cũng khó bắt đầu",
        "chọn một nguyên tắc đủ dùng để xếp việc hôm nay",
        "Ví dụ: Bạn quyết làm việc có hạn trước thay vì cân lại toàn bộ danh sách mỗi giờ.",
    ),
    "pentacles-ace": (
        "một điều kiện thực tế được chuẩn bị có thể giảm công sức cho cả ngày",
        "mua thêm đồ mà không xử lý bất tiện đang có",
        "đặt vật bạn thường cần ở chỗ dễ lấy trước lượt làm tiếp theo",
        "Ví dụ: Bạn hay phải tìm chìa khóa lúc ra ngoài và muốn dành một chỗ cố định để cất.",
    ),
    "pentacles-2": (
        "đổi giữa nhiều việc cần tính cả công sức chuyển sự chú ý",
        "coi vài phút trống là đủ để chen thêm một việc nữa",
        "làm hai việc cùng loại trong một lượt thay vì đổi liên tục",
        "Ví dụ: Bạn chạy mua đồ nhiều lần trong ngày và có thể gộp danh sách cho một chuyến.",
    ),
    "pentacles-3": (
        "chia việc theo khả năng giúp công sức của từng người được dùng đúng chỗ",
        "làm lại phần đã giao vì không thống nhất cách nhận kết quả",
        "hỏi ai nhận được phần nào và chọn một cách bàn giao đơn giản",
        "Ví dụ: Cả nhà chuẩn bị bữa ăn nhưng hai người cùng rửa rau còn việc khác chưa ai làm.",
    ),
    "pentacles-4": (
        "giữ một phần thời gian trống là cách bảo toàn sức cho việc bất ngờ",
        "giữ sức bằng cách né cả hoạt động mình thật sự muốn",
        "chọn một khoảng không nhận lịch và một hoạt động vẫn muốn giữ",
        "Ví dụ: Bạn muốn cuối tuần bớt kín nhưng vẫn thích một lịch gặp ngắn với bạn thân.",
    ),
    "pentacles-5": (
        "thiếu hỗ trợ có thể làm việc nhỏ cũng tốn sức hơn bình thường",
        "tự chịu bất tiện rồi xem khó khăn ấy là lỗi của mình",
        "hỏi một người hoặc nơi có thể giúp đúng điều bạn đang thiếu",
        "Ví dụ: Bạn phải mang nhiều đồ lên nhà và có thể nhờ người cùng nhà giữ giúp cửa.",
    ),
    "pentacles-6": (
        "nhận hỗ trợ cũng có thể giúp giữ sức chứ không chỉ cho đi",
        "giúp liên tục nhưng từ chối mọi lời giúp lại",
        "chọn một việc có thể nhận hỗ trợ và nói rõ phần bạn cần",
        "Ví dụ: Bạn thường chở mọi người, nhưng lần này có thể nhờ một người đón mình.",
    ),
    "pentacles-7": (
        "một cách dùng sức cần thời gian và dấu hiệu thực tế để đánh giá",
        "đổi lịch mỗi ngày nên không biết cách nào làm mình đỡ mệt",
        "giữ một thay đổi nhỏ vài ngày rồi ghi điều bạn nhận thấy",
        "Ví dụ: Sau vài lần không xếp buổi hẹn sát nhau, bạn muốn xem mình có còn vội như trước.",
    ),
    "pentacles-8": (
        "kỹ năng quen hơn có thể giúp một việc cần ít công sức hơn",
        "luyện quá lâu một lượt khiến lỗi nhỏ bắt đầu tăng",
        "thử một lượt ngắn có điểm dừng và sửa đúng một thao tác",
        "Ví dụ: Bạn tập gõ nhanh nhưng lúc mệt bắt đầu sai nhiều hơn và cần dừng lượt tập.",
    ),
    "pentacles-9": (
        "tự sắp xếp khoảng riêng giúp bạn nhận ra cách nghỉ phù hợp mình",
        "coi việc tự lo được là lý do không bao giờ nhờ ai",
        "chọn một khoảng nghỉ theo ý mình và nhận giúp đỡ nếu cần",
        "Ví dụ: Bạn có buổi sáng riêng nhưng vẫn có thể nhờ người khác lấy giúp một món đồ.",
    ),
    "pentacles-10": (
        "cách phân việc trong nhà ảnh hưởng sức của bạn qua nhiều ngày",
        "giữ lệ cũ dù một người đang làm phần lớn việc chung",
        "viết các việc lặp lại và hỏi cách chia bền hơn",
        "Ví dụ: Việc mua đồ và dọn bếp luôn rơi vào bạn nên cả tuần không có buổi tối trống.",
    ),
    "pentacles-page": (
        "quan sát một thói quen nhỏ giúp biết công sức đang được dùng thế nào",
        "theo dõi quá nhiều mục khiến việc ghi chép thành gánh mới",
        "viết một hoạt động tốn sức và một điều giúp bạn thấy nhẹ hơn",
        "Ví dụ: Khi có nhiều cuộc gọi trong ngày, bạn muốn ghi lại mức chú ý khác ngày yên "
        "tĩnh ra sao.",
    ),
    "pentacles-knight": (
        "mức cố gắng vừa phải và đều có thể dễ giữ hơn một lượt dồn sức",
        "cố giữ đủ lượng việc dù điều kiện hôm nay thay đổi",
        "giữ một việc nhỏ có ích và giảm phần thêm khi ít sức",
        "Ví dụ: Bạn thường dọn nhà một chút mỗi tối, nhưng lúc bận chỉ cần cất đồ đang dùng.",
    ),
    "pentacles-queen": (
        "chuẩn bị nhu cầu cơ bản giúp bạn bớt phải xoay xở lúc đã mệt",
        "lo sẵn cho người khác nhưng không để phần thuận tiện cho mình",
        "chọn một việc chuẩn bị giúp chính bạn trong buổi tiếp theo",
        "Ví dụ: Bạn đã xếp đồ cho mọi người nhưng phần đồ mình cần sáng mai vẫn chưa sẵn.",
    ),
    "pentacles-king": (
        "dùng nguồn lực sẵn có có thể giảm việc phải tự gánh lâu dài",
        "chọn tự làm mọi thứ dù có cách chia việc phù hợp",
        "xem một nguồn hỗ trợ có sẵn và chọn phần nên dùng",
        "Ví dụ: Bạn có người cùng lo việc nhà nhưng vẫn tự nhận cả phần chuẩn bị mỗi tuần.",
    ),
}

_SELF_CARE: dict[str, _Entry] = {
    "major-fool": (
        "chăm mình có thể bắt đầu bằng một thử nghiệm nhỏ, chưa cần kế hoạch hoàn hảo",
        "đặt mục tiêu đổi hết sinh hoạt rồi ngại bắt đầu",
        "chọn một việc nhỏ dễ chịu để thử trong hôm nay",
        "Ví dụ: Bạn muốn dành thời gian riêng nhưng có thể bắt đầu bằng mười phút đọc lúc rảnh.",
    ),
    "major-magician": (
        "những thứ đã có có thể đủ cho một cách chăm mình thiết thực",
        "đợi mua đủ đồ hoặc đủ điều kiện mới cho mình nghỉ",
        "chọn một món sẵn có cho hoạt động bạn muốn dành riêng cho mình",
        "Ví dụ: Khi muốn viết vài dòng cho mình, bạn cứ đợi mua sổ mới dù đã có giấy.",
    ),
    "major-high-priestess": (
        "nhu cầu riêng đáng được nhận ra trước khi hỏi người khác mình nên muốn gì",
        "coi ý kiến bên ngoài là câu trả lời thay cho cảm nhận của mình",
        "viết điều bạn đang muốn và điều bạn không muốn nhận lúc này",
        "Ví dụ: Mọi người rủ đi chơi nhưng bạn muốn tối yên tĩnh và chưa nói điều đó.",
    ),
    "major-empress": (
        "sự thoải mái của bạn cũng đáng được chăm bằng những điều cụ thể",
        "để mọi thứ dễ chịu cho người khác còn phần mình luôn chờ sau",
        "chọn một nhu cầu cơ bản của mình để lo trước việc giúp thêm",
        "Ví dụ: Bạn chuẩn bị bữa cho mọi người nhưng món mình muốn ăn lại luôn bị bỏ qua.",
    ),
    "major-emperor": (
        "giới hạn rõ bảo vệ thời gian bạn đã dành cho bản thân",
        "biến lịch chăm mình thành bộ luật khiến mình thấy có lỗi khi lệch",
        "đặt một khoảng riêng có thể giữ và cho phép đổi cách sử dụng",
        "Ví dụ: Bạn dành tối thứ tư cho mình nhưng có thể đọc hoặc ngồi nghỉ tùy lúc ấy muốn gì.",
    ),
    "major-hierophant": (
        "cách chăm mình nên được chọn theo nhu cầu, không chỉ theo lời truyền nhau",
        "làm theo một thói quen được khen dù mình không thấy phù hợp",
        "hỏi bản thân một thói quen đang giúp điều gì rồi chọn giữ hay đổi",
        "Ví dụ: Khi thử viết sổ mỗi sáng theo lời khuyên, bạn nhận ra viết tối hợp mình hơn.",
    ),
    "major-lovers": (
        "chăm mình cũng là chọn điều phù hợp giá trị của bạn",
        "bỏ điều quan trọng với mình để được người khác đồng ý",
        "viết một điều bạn muốn giữ trong lựa chọn đang cân nhắc",
        "Ví dụ: Bạn muốn giữ cuối tuần cho gia đình nhưng ngại từ chối người mời mình tham gia "
        "hoạt động khác.",
    ),
    "major-chariot": (
        "bạn có thể chủ động dành chỗ cho một nhu cầu đã bị để sau",
        "coi chăm mình như cuộc đua phải hoàn thành đủ mục",
        "chọn một việc cho bản thân và đặt nó vào lịch hôm nay",
        "Ví dụ: Bạn muốn có buổi đọc riêng nhưng cứ đợi mọi việc nhà xong mới tính.",
    ),
    "major-strength": (
        "đối xử nhẹ với mình giúp sửa việc khó mà không tự hạ thấp",
        "dùng lời trách để ép mình làm tốt hơn",
        "viết lại một câu tự trách thành mô tả việc có thể sửa",
        "Ví dụ: Khi quên cuộc hẹn, bạn gọi mình vô dụng thay vì nghĩ cách đặt lời nhắc.",
    ),
    "major-hermit": (
        "khoảng riêng giúp bạn nghe được mong muốn không bị ý kiến khác lấn át",
        "ở riêng quá lâu dù thật ra muốn có người để kể",
        "chọn lúc ở một mình và lúc liên lạc với người bạn tin",
        "Ví dụ: Sau lúc nghĩ riêng về buổi gặp, bạn vẫn muốn gọi cho bạn thân vào ngày mai.",
    ),
    "major-wheel-of-fortune": (
        "cách chăm mình cần linh hoạt khi hoàn cảnh sinh hoạt đổi",
        "tự trách vì không giữ được thói quen trong một tuần khác thường",
        "chọn phiên bản đơn giản hơn của một thói quen còn muốn giữ",
        "Ví dụ: Khi đi xa, bạn không có góc đọc quen nhưng có thể dành vài phút đọc ở nơi nghỉ.",
    ),
    "major-justice": (
        "công bằng với mình là tính cả nhu cầu của bạn trong việc chung",
        "đặt tiêu chuẩn cho mình cao hơn mức mình đòi người khác",
        "so điều bạn đang tự yêu cầu với lời bạn sẽ nói cho một người bạn",
        "Ví dụ: Bạn cho người khác nghỉ khi mệt nhưng nghĩ mình phải làm xong mọi việc mới "
        "được dừng.",
    ),
    "major-hanged-man": (
        "không làm theo cách cũ có thể giúp bạn nhận ra điều mình thật sự cần",
        "trì hoãn nhu cầu của mình mãi để chờ lúc thuận tiện cho tất cả",
        "thử một cách khác cho việc chăm mình thường bị hoãn",
        "Ví dụ: Bạn không có cả buổi đi chơi riêng nhưng có thể chọn một cuộc dạo ngắn lúc rảnh.",
    ),
    "major-death": (
        "có thể bỏ một yêu cầu về bản thân không còn hợp giai đoạn hiện tại",
        "giữ hình ảnh cũ dù nó khiến mình phải cố quá nhiều",
        "chọn một tiêu chuẩn cũ bạn muốn ngừng áp cho mình",
        "Ví dụ: Bạn từng thích tổ chức mọi cuộc gặp nhưng lúc này không muốn tiếp tục nhận vai đó.",
    ),
    "major-temperance": (
        "chăm mình có thể vừa đủ mà không cần bỏ hết trách nhiệm khác",
        "đợi rảnh hoàn toàn mới cho mình một phần dễ chịu",
        "chọn một việc chăm mình vừa với lịch thay vì hoãn cả kế hoạch",
        "Ví dụ: Khi không có ngày nghỉ trọn vẹn, bạn vẫn muốn dành một bữa ăn thong thả.",
    ),
    "major-devil": (
        "một lời đồng ý không tự nguyện đáng được xem lại",
        "đổi sự thoải mái của mình lấy cảm giác được cần đến",
        "nói không với một yêu cầu bạn không muốn nhận",
        "Ví dụ: Bạn định nhận thêm việc giúp chỉ vì ngại người kia thất vọng dù mình muốn từ chối.",
    ),
    "major-tower": (
        "khi kế hoạch bị phá vỡ, nhu cầu trước mắt đáng được lo trước",
        "ép mình giải quyết mọi hậu quả ngay lúc còn bối rối",
        "chọn điều cần lo trước và nhờ một người tin cậy giúp phần còn lại",
        "Ví dụ: Lịch đi lại bị đổi đột ngột, bạn cần chỗ ngồi chờ trước khi sắp xếp việc tiếp "
        "theo.",
    ),
    "major-star": (
        "bạn có thể cho mình một điều dễ chịu mà chưa cần chứng minh đã ổn",
        "biến chăm mình thành yêu cầu phải thấy vui hơn ngay",
        "chọn một việc nhẹ bạn muốn làm, không đặt mục tiêu phải đổi cảm xúc",
        "Ví dụ: Sau một việc không như ý, bạn muốn ngồi nghe nhạc mà chưa cần ép mình vui.",
    ),
    "major-moon": (
        "không rõ mình muốn gì là lúc có thể trì hoãn một quyết định không gấp",
        "coi nỗi sợ là bằng chứng mình nên từ bỏ điều đang muốn",
        "viết điều đã biết và điều còn lo trước khi chọn",
        "Ví dụ: Bạn chưa biết nhận lời một chuyến đi hay không và có thể hỏi thêm lịch cụ thể.",
    ),
    "major-sun": (
        "niềm vui của bạn không cần được chứng minh là hữu ích mới có giá trị",
        "thấy có lỗi khi làm điều vui mà không tạo ra kết quả",
        "chọn một hoạt động bạn thích chỉ vì nó khiến bạn vui",
        "Ví dụ: Bạn muốn chơi một trò đơn giản nhưng cứ nghĩ phải dùng lúc rảnh để học thêm.",
    ),
    "major-judgement": (
        "nhìn lại bản thân có thể dẫn đến một lựa chọn mới thay vì một bản án",
        "lấy lỗi cũ làm lý do không cho mình thử lại",
        "viết điều đã học và một thay đổi nhỏ cho lần thử tiếp",
        "Ví dụ: Bạn bỏ dở sở thích trước đây nhưng lần này có thể bắt đầu với lịch nhẹ hơn.",
    ),
    "major-world": (
        "chấp nhận phần đã hoàn thành cho phép bạn tận hưởng mà không sửa thêm",
        "đòi bản thân phải hoàn hảo trước khi thấy hài lòng",
        "chọn một việc đã đủ tốt và để nó được kết thúc",
        "Ví dụ: Bạn đã làm xong món quà thủ công nhưng vẫn sửa từng góc dù người nhận rất thích.",
    ),
    "wands-ace": (
        "điều khiến bạn háo hức cũng đáng có chỗ trong cuộc sống riêng",
        "gạt sở thích vì nghĩ nó chưa đủ nghiêm túc",
        "chọn một lần thử cho sở thích bạn đang muốn khám phá",
        "Ví dụ: Bạn muốn học làm đồ đất sét nhưng ngại vì mọi người cho đó là việc trẻ con.",
    ),
    "wands-2": (
        "chọn điều muốn dành cho mình giúp chăm sóc không chỉ nằm trong dự định",
        "lên kế hoạch rất đẹp nhưng không dành thời gian thật",
        "đặt một hoạt động riêng vào khoảng trống có thật trong tuần",
        "Ví dụ: Bạn có danh sách nơi muốn đi nhưng chưa chọn lịch cho một buổi dành riêng.",
    ),
    "wands-3": (
        "một thay đổi cho bản thân cần thời gian để biết có hợp không",
        "bỏ ngay cách mới vì lần đầu chưa thấy khác",
        "thử lại điều đã chọn vào một dịp khác rồi xem cảm nhận của mình",
        "Ví dụ: Bạn thử đi chơi một mình lần đầu chưa quen và có thể chọn nơi gần hơn lần sau.",
    ),
    "wands-4": (
        "một góc thuộc về bạn có thể là nơi tận hưởng mà không phải phục vụ ai",
        "chỉ tạo không gian dễ chịu khi có khách đến",
        "chọn và dọn một chỗ nhỏ để dùng cho hoạt động mình thích",
        "Ví dụ: Bạn kê ghế đẹp cho khách nhưng lúc đọc riêng lại ngồi ở góc chật.",
    ),
    "wands-5": (
        "chăm mình không cần theo cùng cách với những người xung quanh",
        "so thói quen của mình với người khác rồi xem đó là cuộc thi",
        "chọn một cách phù hợp bạn dù nó khác cách đang được khen",
        "Ví dụ: Bạn thích nghỉ ở nhà nhưng nhóm bạn đều khoe lịch hoạt động kín cuối tuần.",
    ),
    "wands-6": (
        "tiến bộ của bạn đáng được ghi nhận ngay cả khi chưa ai khen",
        "chỉ cho mình nghỉ hoặc vui sau khi được công nhận",
        "viết một điều bạn đã làm tốt và tự dành một lời ghi nhận cụ thể",
        "Ví dụ: Bạn giữ được lời hẹn với mình trong tuần nhưng ngại coi việc nhỏ đó là đáng mừng.",
    ),
    "wands-7": (
        "nhu cầu của bạn vẫn có giá trị khi người khác không đồng ý",
        "xin phép quá nhiều cho một giới hạn cá nhân",
        "nói giới hạn của bạn mà không biến nó thành câu hỏi xin chấp thuận",
        "Ví dụ: Bạn muốn giữ một tối không hẹn nhưng đang ngại người khác nghĩ mình khó gần.",
    ),
    "wands-8": (
        "bạn được quyền chọn tốc độ trả lời thay vì luôn phải sẵn sàng",
        "coi mọi thông báo là yêu cầu phải đáp ngay",
        "đặt một lúc xem tin và báo trước nếu có người đang chờ việc quan trọng",
        "Ví dụ: Tin nhắn đến khi bạn đang ăn và bạn có thể trả lời sau bữa.",
    ),
    "wands-9": (
        "giữ giới hạn sau chuyện khó không có nghĩa phải cảnh giác với mọi người",
        "từ chối cả lời hỗ trợ mình muốn vì sợ lặp chuyện cũ",
        "chọn một sự giúp đỡ nhỏ và nói điều kiện khiến bạn thoải mái",
        "Ví dụ: Bạn từng khó chịu khi nhận giúp, nhưng lần này có thể nhờ đúng một việc rõ ràng.",
    ),
    "wands-10": (
        "trách nhiệm với người khác không xóa nhu cầu được chia bớt việc của bạn",
        "nghĩ chỉ khi làm hết mới xứng đáng được chăm",
        "nói một việc bạn muốn chia lại và giữ thời gian riêng đã định",
        "Ví dụ: Bạn lo mọi việc cho buổi gặp và muốn một người khác nhận phần dọn sau đó.",
    ),
    "wands-page": (
        "bạn có thể khám phá điều mình thích mà chưa cần giỏi",
        "tự chê vụng nên không cho mình chơi thử",
        "thử một hoạt động mới với mục tiêu tìm hiểu chứ không chấm điểm",
        "Ví dụ: Bạn muốn học chụp ảnh và có thể thử chụp một món đồ lúc rảnh.",
    ),
    "wands-knight": (
        "mong muốn đổi mới cần một cam kết vừa sức với bản thân",
        "hứa đổi toàn bộ đời sống trong một lúc hào hứng",
        "chọn một thay đổi nhỏ còn đường điều chỉnh",
        "Ví dụ: Khi muốn đi chơi mỗi cuối tuần, bạn có thể bắt đầu bằng một buổi trong tháng.",
    ),
    "wands-queen": (
        "bạn có thể thể hiện sở thích mà không cần làm mình nhỏ lại",
        "cố tỏ ra dễ mến bằng cách bỏ điều mình thật sự thích",
        "chọn một điều muốn mặc hoặc muốn làm theo ý mình",
        "Ví dụ: Lúc chọn đồ đi gặp nhóm, bạn thích áo nhiều màu nhưng ngại khác sở thích mọi "
        "người.",
    ),
    "wands-king": (
        "tự quyết cuộc sống riêng cần hướng bạn muốn chứ không chỉ kỳ vọng bên ngoài",
        "lập mục tiêu cho mình bằng tiêu chuẩn của người có hoàn cảnh khác",
        "viết một ưu tiên do bạn chọn và bỏ bớt mục tiêu không còn muốn",
        "Ví dụ: Bạn muốn có thời gian cho sở thích nhưng đang theo lịch thành tích của người khác.",
    ),
    "cups-ace": (
        "cảm xúc của bạn có thể được nhận ra mà chưa cần phán đúng sai",
        "bác cảm giác của mình vì nghĩ việc ấy không đủ lớn",
        "gọi tên cảm xúc bằng lời đơn giản và viết điều bạn muốn lúc này",
        "Ví dụ: Khi một chuyện nhỏ làm bạn buồn, bạn lại nghĩ mình không được phép thấy vậy.",
    ),
    "cups-2": (
        "sự chăm sóc có thể được nhận từ người bạn thấy tin cậy",
        "luôn nhận vai người giúp rồi ngại nói mình cũng cần",
        "hỏi một người tin cậy về một sự hỗ trợ bạn muốn nhận",
        "Ví dụ: Khi thường nghe bạn thân kể, bạn cũng muốn có một lượt được họ nghe chuyện của "
        "mình.",
    ),
    "cups-3": (
        "kết nối vui vẻ có thể là một phần chăm mình nếu bạn được là mình",
        "đi cùng nhóm chỉ vì sợ bị bỏ ngoài dù không thấy thoải mái",
        "chọn gặp những người bạn có thể nói thật về nhu cầu của mình",
        "Ví dụ: Bạn muốn gặp nhóm thân nơi mọi người chấp nhận bạn về sớm mà không trêu.",
    ),
    "cups-4": (
        "không muốn nhận một lời mời vẫn là lựa chọn hợp lệ",
        "nhận lời vì người mời nhiệt tình rồi thấy khó chịu với chính mình",
        "nói lời từ chối ngắn cho một hoạt động bạn chưa muốn",
        "Ví dụ: Người quen rủ dự sự kiện, nhưng bạn muốn dành buổi đó cho việc riêng.",
    ),
    "cups-5": (
        "bạn có thể buồn về phần mất mà chưa cần tìm mặt tích cực ngay",
        "tự ép biết ơn để khỏi phải thừa nhận thất vọng",
        "viết điều khiến bạn tiếc và chọn một cách chăm mình hôm nay",
        "Ví dụ: Chuyến đi bị hủy, bạn muốn dành một lúc buồn trước khi lên kế hoạch khác.",
    ),
    "cups-6": (
        "điều từng làm bạn thấy được chăm có thể gợi một nhu cầu hiện tại",
        "đòi người hiện tại lặp đúng cách chăm sóc của người trong ký ức",
        "chọn một điều bạn nhớ thích và xem mình có muốn làm cho mình không",
        "Ví dụ: Bạn nhớ những lần được nấu món quen và muốn tự chuẩn bị món đó cuối tuần.",
    ),
    "cups-7": (
        "cách chăm mình cần được chọn theo nhu cầu, không theo hình ảnh lý tưởng",
        "mua hoặc đăng ký nhiều thứ để có cảm giác đang chăm mình",
        "hỏi mình đang cần điều gì trước khi chọn thêm một hoạt động",
        "Ví dụ: Bạn xem nhiều gói trải nghiệm nhưng điều muốn nhất lúc này chỉ là một tối "
        "không hẹn.",
    ),
    "cups-8": (
        "bạn có thể ngừng một hoạt động không còn đáp ứng nhu cầu riêng",
        "tiếp tục một lời hẹn với bản thân chỉ vì từng rất thích nó",
        "nói rõ điều muốn ngừng và chọn cách khác phù hợp hơn",
        "Ví dụ: Lớp học từng vui nay không hợp lịch, bạn muốn xem lại việc có tiếp tục tham "
        "gia không.",
    ),
    "cups-9": (
        "sở thích riêng không cần người khác thấy giống bạn mới đáng được giữ",
        "xin người khác xác nhận mọi niềm vui của mình",
        "chọn một điều bạn thích và tận hưởng mà không cần đăng để được khen",
        "Ví dụ: Bạn thích ngồi chăm cây lúc rảnh dù bạn bè không thấy hoạt động đó thú vị.",
    ),
    "cups-10": (
        "sự thuộc về nên có chỗ cho nhu cầu của bạn chứ không chỉ hòa thuận bên ngoài",
        "giấu điều khó chịu để giữ hình ảnh gia đình hoặc nhóm luôn vui",
        "nói một điều giúp bạn thấy thoải mái hơn trong không gian chung",
        "Ví dụ: Bạn muốn có chỗ ngồi riêng trong nhà nhưng cứ nhường vì ngại mọi người không vui.",
    ),
    "cups-page": (
        "đối xử dịu với phần vụng về giúp bạn thử điều mình thích",
        "xấu hổ về mong muốn nhỏ vì cho rằng mình phải trưởng thành hơn",
        "viết một điều nhỏ bạn muốn mà không tự chê nó",
        "Ví dụ: Bạn muốn giữ một món đồ đáng yêu trên bàn nhưng sợ người khác thấy trẻ con.",
    ),
    "cups-knight": (
        "sự quan tâm cho bản thân có thể thành một lời hẹn bạn thật sự muốn giữ",
        "lập buổi chăm mình cầu kỳ rồi thấy thất bại khi không làm đủ",
        "chọn một hoạt động dễ thực hiện để dành riêng cho mình",
        "Ví dụ: Lúc muốn có buổi tối dễ chịu, bạn chọn món thích thay vì chuẩn bị đủ mọi thứ.",
    ),
    "cups-queen": (
        "quan tâm cảm xúc của người khác vẫn cần ranh giới cho phần của bạn",
        "xem việc làm mọi người vui là trách nhiệm riêng mình",
        "nói điều bạn giúp được và điều cần để người kia tự xử lý",
        "Ví dụ: Người thân buồn và bạn muốn ở cạnh nhưng không thể quyết định thay họ.",
    ),
    "cups-king": (
        "bạn có thể thừa nhận cảm xúc mà không phải mất quyền chọn cách đáp lại",
        "lấy vẻ bình tĩnh làm lý do phủ nhận điều mình cần",
        "viết điều đang cảm thấy rồi chọn một nhu cầu muốn ưu tiên",
        "Ví dụ: Bạn nói mình ổn sau cuộc gặp khó nhưng thật ra muốn một lúc không bị hỏi thêm.",
    ),
    "swords-ace": (
        "nhu cầu được gọi rõ giúp bạn không phải chờ người khác đoán",
        "dùng một nhãn chê mình thay cho mô tả điều còn thiếu",
        "viết một câu bắt đầu bằng mình cần và nêu điều cụ thể",
        "Ví dụ: Bạn đang gọi mình khó tính trong khi điều cần là người khác báo trước khi đổi "
        "lịch.",
    ),
    "swords-2": (
        "bạn có thể xin thời gian trước một lựa chọn liên quan nhu cầu riêng",
        "quyết cho xong để tránh áp lực dù chưa biết mình muốn gì",
        "nói bạn cần thêm thời gian và hỏi một thông tin giúp lựa chọn",
        "Ví dụ: Khi nhận lời mời cần xác nhận, bạn chưa biết có giữ được thời gian riêng không.",
    ),
    "swords-3": (
        "điều làm bạn đau lòng đáng được nhận ra mà không cần tự trách",
        "xem một lời chê là sự thật về giá trị con người mình",
        "tách câu người khác đã nói khỏi điều bạn biết về mình",
        "Ví dụ: Khi bị chê một lựa chọn, bạn quên rằng mình có lý do riêng để chọn như vậy.",
    ),
    "swords-4": (
        "nghỉ là nhu cầu có thể được đáp ứng trước khi mọi việc hoàn hảo",
        "đặt thêm điều kiện mỗi lần mình sắp được nghỉ",
        "đặt một khoảng không nhận việc và chọn cách nghỉ bạn muốn",
        "Ví dụ: Lúc định ngồi nghỉ, bạn lại nghĩ phải dọn thêm một chỗ nữa mới được phép.",
    ),
    "swords-5": (
        "không tham gia một cuộc hơn thua có thể là cách giữ sự tôn trọng với mình",
        "cố chứng minh giá trị bản thân bằng cách thắng người đang chê",
        "rời một cuộc tranh luận không còn tôn trọng bạn nếu có thể",
        "Ví dụ: Khi bị kéo vào cuộc so ai thành công hơn, bạn không muốn tiếp tục trả lời.",
    ),
    "swords-6": (
        "chọn một không gian dễ chịu hơn không cần phủ nhận điều đã trải qua",
        "cho rằng rời chỗ không hợp là mình không chịu được khó",
        "chọn một nơi hoặc cách tham gia khiến bạn thấy thoải mái hơn",
        "Ví dụ: Khi buổi gặp quá ồn, bạn muốn chuyển sang bàn yên hơn mà không xin lỗi nhiều lần.",
    ),
    "swords-7": (
        "quyền riêng tư cho phép bạn không kể mọi điều để được chấp nhận",
        "nói sai điều mình muốn chỉ để tránh câu hỏi tiếp theo",
        "nói phần bạn muốn giữ riêng thay vì tạo một câu chuyện khác",
        "Ví dụ: Có người hỏi chuyện riêng và bạn muốn từ chối kể thay vì nghĩ một lời giải "
        "thích giả.",
    ),
    "swords-8": (
        "những điều tự cấm mình có thể được xem lại từng điều một",
        "coi cảm giác có lỗi là bằng chứng mình không được đặt nhu cầu riêng",
        "viết một điều mình nghĩ không được làm và kiểm tra lý do cụ thể",
        "Ví dụ: Bạn nghĩ không được từ chối giúp người khác nhưng chưa hỏi vì sao mình phải "
        "luôn nhận.",
    ),
    "swords-9": (
        "lo lắng về một chuyện không cần biến thành lời buộc tội bản thân",
        "dùng khả năng xấu nhất để đánh giá cả con người mình",
        "viết điều đã xảy ra và tách khỏi điều đang lo chưa có bằng chứng",
        "Ví dụ: Bạn quên trả lời một tin nhắn và đang tưởng tượng mọi người đều ghét mình.",
    ),
    "swords-10": (
        "một trải nghiệm đã quá sức không cần được kéo dài để chứng minh bạn đủ cố gắng",
        "xem việc dừng lại là thất bại về bản thân",
        "dừng phần không cần tiếp tục và chọn một người tin cậy để nhờ hỗ trợ",
        "Ví dụ: Bạn đã cố làm một hoạt động đến mức rất mệt và muốn nhờ người khác nhận phần "
        "còn lại.",
    ),
    "swords-page": (
        "tìm hiểu nhu cầu bản thân cần câu hỏi thật hơn là soi lỗi liên tục",
        "theo dõi mình như bài kiểm tra phải đạt đủ điểm",
        "hỏi một điều giúp biết mình muốn gì mà không chấm đúng sai",
        "Ví dụ: Bạn ghi sinh hoạt mỗi ngày nhưng muốn xem điều nào dễ chịu thay vì chỉ đếm lần "
        "làm sai.",
    ),
    "swords-knight": (
        "muốn sửa mình nhanh vẫn cần chọn thay đổi không làm mình quá sức",
        "vừa nhận góp ý đã áp hàng loạt yêu cầu mới cho bản thân",
        "chọn một góp ý có ích và để phần khác chờ",
        "Ví dụ: Sau một lời nhận xét, bạn định đổi ngay cách ăn mặc, nói chuyện và lịch sinh hoạt.",
    ),
    "swords-queen": (
        "lời từ chối rõ giúp bạn giữ quyền quyết định điều thuộc về mình",
        "nghĩ phải có lý do thật nghiêm trọng mới được nói không",
        "nói điều bạn không muốn nhận bằng câu ngắn, không tự hạ thấp",
        "Ví dụ: Khi có người hỏi mượn đồ riêng, bạn muốn từ chối dù món đó không đắt.",
    ),
    "swords-king": (
        "tiêu chuẩn bạn đặt cho mình cần hợp lý và có chỗ cho hoàn cảnh thực tế",
        "dùng một ngày không đạt để kết luận mình thiếu kỷ luật",
        "kiểm tra một yêu cầu tự đặt có còn phù hợp rồi sửa nếu cần",
        "Ví dụ: Bạn muốn đọc mỗi ngày nhưng lịch mới khiến mục tiêu cũ không còn vừa sức.",
    ),
    "pentacles-ace": (
        "chăm mình có thể bắt đầu bằng một điều kiện cơ bản được đáp ứng",
        "mua thêm đồ thay vì lo nhu cầu đang thiếu rõ nhất",
        "chọn một nhu cầu thực tế của bạn để chuẩn bị hôm nay",
        "Ví dụ: Bạn tìm đồ trang trí mới trong khi góc ngồi riêng vẫn chưa có chỗ đặt sách.",
    ),
    "pentacles-2": (
        "nhu cầu riêng cần được tính vào lịch chứ không chỉ chen vào chỗ còn thừa",
        "đổi giờ dành cho mình mỗi khi có người nhờ",
        "đặt một khoảng cho bản thân và đổi một lịch ít quan trọng hơn nếu cần",
        "Ví dụ: Bạn đã định đi mua món cần dùng nhưng liên tục dời để nhận việc giúp khác.",
    ),
    "pentacles-3": (
        "bạn có thể nhờ hỗ trợ mà vẫn giữ quyền chọn cách mình muốn được giúp",
        "nhận giúp rồi thấy phải làm theo mọi ý kiến của người giúp",
        "nói rõ phần cần hỗ trợ và phần bạn muốn tự quyết",
        "Ví dụ: Bạn nhờ người thân sắp góc riêng nhưng vẫn muốn tự chọn đồ sẽ giữ lại.",
    ),
    "pentacles-4": (
        "giữ đồ, tiền và thời gian riêng cần ranh giới phù hợp nhu cầu của bạn",
        "không dám dùng cả thứ đã dành cho mình vì sợ thiếu về sau",
        "chọn một nguồn lực riêng có thể dùng mà không ảnh hưởng việc thiết yếu",
        "Ví dụ: Bạn đã dành một buổi cho sở thích nhưng vẫn ngại sử dụng vì sợ có người cần nhờ.",
    ),
    "pentacles-5": (
        "khi thiếu điều kiện, nhu cầu được hỗ trợ không phải điều đáng xấu hổ",
        "giấu điều đang thiếu để trông như luôn tự lo được",
        "hỏi một nguồn hỗ trợ phù hợp với nhu cầu cụ thể của bạn",
        "Ví dụ: Bạn thiếu người giúp chuyển đồ và có thể nhờ nhóm quen thay vì cố tự làm.",
    ),
    "pentacles-6": (
        "chăm mình bao gồm việc cho và nhận trong mức bạn thấy tự nguyện",
        "cho quá mức rồi nghĩ mình phải ngại khi cần giúp lại",
        "nói phần bạn có thể giúp và phần bạn muốn nhận hỗ trợ",
        "Ví dụ: Bạn hay lo bữa ăn cho nhóm và lần này muốn nhờ một người khác chuẩn bị.",
    ),
    "pentacles-7": (
        "một thói quen chăm mình cần được xem theo ích lợi thật chứ không chỉ số ngày đã giữ",
        "cố tiếp tục một cách không hợp vì tiếc công đã bỏ",
        "hỏi điều đã chọn có giúp nhu cầu của bạn không rồi sửa một phần",
        "Ví dụ: Sau nhiều lần ghi sổ, bạn muốn đổi cách ghi vì mẫu hiện tại làm mình thấy áp lực.",
    ),
    "pentacles-8": (
        "một việc chăm mình có thể được tập dần thay vì phải làm đúng ngay",
        "xem một ngày bỏ lỡ là lý do bỏ luôn thói quen",
        "chọn lượt thử tiếp theo nhỏ hơn và tập lại phần có ích",
        "Ví dụ: Bạn quên dành thời gian đọc hôm qua nhưng có thể đọc vài trang lúc rảnh hôm nay.",
    ),
    "pentacles-9": (
        "tận hưởng điều mình đã tạo ra là một phần của việc tự chăm",
        "xem mọi thời gian không làm việc là lãng phí",
        "dành một khoảng để dùng hoặc tận hưởng điều bạn đã chuẩn bị cho mình",
        "Ví dụ: Bạn đã chăm cây nhiều tháng nhưng chưa có lúc ngồi ngắm góc cây mình thích.",
    ),
    "pentacles-10": (
        "nhu cầu của bạn cần chỗ trong thỏa thuận chung lâu dài",
        "giữ lệ gia đình bằng cách để phần riêng luôn đứng cuối",
        "nói một thay đổi trong việc chung để bạn có thời gian chăm mình",
        "Ví dụ: Cả nhà quen bạn lo việc nấu bữa cuối tuần nhưng bạn muốn chia lại để có một "
        "buổi riêng.",
    ),
    "pentacles-page": (
        "học cách chăm mình có thể bắt đầu từ việc quan sát điều phù hợp bản thân",
        "tìm công thức đúng cho tất cả rồi bỏ qua trải nghiệm của mình",
        "thử một việc nhỏ và viết điều bạn thấy hợp hoặc không hợp",
        "Ví dụ: Bạn thử dành lúc sáng cho sở thích và muốn xem mình thích giờ đó hay giờ tối.",
    ),
    "pentacles-knight": (
        "sự chăm sóc đáng tin đến từ lời hẹn nhỏ bạn có thể giữ với mình",
        "giữ lịch chỉ để không đứt chuỗi dù đã không còn thấy phù hợp",
        "chọn một thói quen dễ giữ và cho phép điều chỉnh khi lịch đổi",
        "Ví dụ: Bạn thường chuẩn bị đồ tối hôm trước nhưng có thể đổi giờ khi về nhà muộn.",
    ),
    "pentacles-queen": (
        "bạn cũng cần được lo bằng sự chu đáo mình dành cho người khác",
        "chăm mọi người rồi coi nhu cầu mình là phần tùy chọn",
        "chuẩn bị một điều cần cho chính bạn trước khi nhận giúp thêm",
        "Ví dụ: Bạn đã xếp chỗ dễ chịu cho mọi người nhưng vẫn chưa chọn chỗ ngồi cho mình.",
    ),
    "pentacles-king": (
        "sự ổn định đến từ thời gian và đồ dùng dành cho nhu cầu của chính bạn",
        "lấy khả năng cung cấp cho người khác làm thước đo duy nhất về mình",
        "chọn một phần thời gian hoặc đồ dùng dành riêng cho nhu cầu của bạn",
        "Ví dụ: Khi luôn để đồ tốt cho khách, bạn muốn giữ một món mình thích để dùng hằng ngày.",
    ),
}

_ENTRIES: dict[str, dict[str, _Entry]] = {
    TarotContext.WORK.value: _WORK,
    TarotContext.COMMUNICATION.value: _COMMUNICATION,
    TarotContext.ENERGY.value: _ENERGY,
    TarotContext.SELF_CARE.value: _SELF_CARE,
}

CONTEXT_READINGS: dict[str, dict[str, tuple[str, str, str]]] = {
    context: {card_id: (row[0], row[1], row[2]) for card_id, row in entries.items()}
    for context, entries in _ENTRIES.items()
}

CONTEXT_SCENES: dict[str, dict[str, str]] = {
    context: {card_id: row[3] for card_id, row in entries.items()}
    for context, entries in _ENTRIES.items()
}
