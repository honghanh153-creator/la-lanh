"""Original Vietnamese editorial meanings, not excerpts or predictions.

Each card has its own meaning, pitfall and action. Do not reconstruct a card
by joining a generic rank description to a generic suit description.
"""

MINOR_READINGS: dict[str, tuple[str, str, str]] = {
    "cups-ace": (
        "bắt đầu đón nhận một cảm xúc mới",
        "vội coi rung động ban đầu là lời hứa",
        "nói một điều bạn thích mà chưa đòi một lời cam kết",
    ),
    "cups-2": (
        "hai người cùng muốn lắng nghe và đáp lại nhau",
        "tưởng mình thích thì người kia cũng phải thích",
        "hỏi xem cả hai có muốn tiếp tục tìm hiểu không",
    ),
    "cups-3": (
        "cảm thấy vui và được đón nhận khi ở cùng bạn bè",
        "để ý kiến của nhóm lấn át cảm nhận của mình",
        "dành một cuộc trò chuyện riêng cho điều bạn chưa nói trước nhóm",
    ),
    "cups-4": (
        "chưa thấy hứng thú với điều đang được đề nghị",
        "gật đầu chỉ vì ngại từ chối",
        "nói rõ bạn chưa muốn nhận lời lúc này",
    ),
    "cups-5": (
        "buồn vì điều đã mất và khó nhìn thấy điều vẫn còn",
        "coi một lần thất vọng là kết luận cho mọi chuyện",
        "kể tên một điều đã mất và một điều bạn vẫn còn",
    ),
    "cups-6": (
        "nhớ cảm giác thân thuộc từ một người hoặc chuyện cũ",
        "chỉ nhớ phần đẹp rồi bỏ qua lý do chuyện cũ kết thúc",
        "viết cả điều bạn nhớ lẫn điều từng khiến bạn không vui",
    ),
    "cups-7": (
        "có nhiều điều muốn nhưng chưa biết điều nào thực tế",
        "thích viễn cảnh hơn những gì đang thật sự có",
        "chọn một mong muốn và kiểm tra nó cần những gì",
    ),
    "cups-8": (
        "nhận ra một chuyện quen thuộc không còn làm mình hài lòng",
        "rời đi chỉ để tránh một cuộc nói chuyện khó",
        "nói rõ điều bạn đang thiếu trước khi quyết định có đi tiếp không",
    ),
    "cups-9": (
        "biết điều gì làm mình vui và đủ với mình",
        "chờ người khác xác nhận rằng mình được phép tận hưởng",
        "dành thời gian cho một việc bạn thích mà không cần khoe với ai",
    ),
    "cups-10": (
        "muốn có một mối quan hệ khiến mình yên tâm và được là mình",
        "giữ hình ảnh hòa thuận dù còn chuyện chưa được nói",
        "hỏi người thân một điều cả hai cần để sống cùng thoải mái hơn",
    ),
    "cups-page": (
        "muốn nói một lời dễ thương nhưng còn ngại",
        "đọc quá nhiều ý nghĩa vào một lời quan tâm nhỏ",
        "nói điều bạn cảm thấy bằng một câu đơn giản",
    ),
    "cups-knight": (
        "muốn thể hiện tình cảm bằng lời nói hoặc một lời mời",
        "hứa lúc đang hào hứng rồi không làm được",
        "chỉ đưa ra một lời hẹn mà bạn thật sự sắp xếp được",
    ),
    "cups-queen": (
        "lắng nghe cảm xúc của mình và quan tâm đến người khác",
        "nhận luôn trách nhiệm làm người khác vui",
        "hỏi người kia cần được nghe hay cần được giúp trước khi làm thay",
    ),
    "cups-king": (
        "giữ bình tĩnh khi nói về một chuyện khiến mình xúc động",
        "giấu hết cảm xúc để trông như mình vẫn ổn",
        "nói một câu về điều bạn đang cảm thấy, không đổ lỗi cho người kia",
    ),
    "wands-ace": (
        "có hứng bắt đầu một việc mới",
        "nhận quá nhiều việc ngay lúc vừa có hứng",
        "chọn một việc nhỏ để thử trước khi nhận thêm",
    ),
    "wands-2": (
        "muốn đi xa hơn nhưng vẫn đang cân nhắc bước đầu",
        "lập kế hoạch mãi mà chưa thử gì",
        "chọn một bước bạn có thể làm với thời gian đang có",
    ),
    "wands-3": (
        "đã bắt đầu và đang chờ xem kế hoạch đi được đến đâu",
        "chỉ chờ phản hồi mà không thống nhất bước tiếp theo",
        "hỏi ai sẽ làm bước tiếp theo và khi nào",
    ),
    "wands-4": (
        "có một cột mốc đáng vui cùng những người đã giúp mình",
        "bỏ qua thành quả vì cứ nhìn sang việc chưa xong",
        "nhắc đến một việc cả nhóm đã làm được và cảm ơn người góp sức",
    ),
    "wands-5": (
        "nhiều người muốn góp ý nhưng đang nói chồng lên nhau",
        "cố thắng tranh luận thay vì giải quyết việc",
        "để từng người nói một ý rồi chốt vấn đề cần giải quyết",
    ),
    "wands-6": (
        "muốn công sức của mình được nhìn nhận",
        "dùng lời khen để đo toàn bộ giá trị của bản thân",
        "ghi lại việc bạn đã làm tốt, kể cả việc chưa được ai khen",
    ),
    "wands-7": (
        "cần bảo vệ một lựa chọn khi có người không đồng ý",
        "coi mọi câu hỏi là một sự công kích",
        "nói lý do lựa chọn của bạn và nghe hết câu hỏi của người kia",
    ),
    "wands-8": (
        "nhiều tin tức hoặc việc mới đến khá nhanh",
        "trả lời ngay khi chưa đọc hết thông tin",
        "đọc lại yêu cầu và xác nhận thời hạn trước khi nhận lời",
    ),
    "wands-9": (
        "đã cố gắng lâu nên vừa muốn tiếp tục vừa thấy mệt",
        "nhận thêm chỉ để chứng minh mình vẫn chịu được",
        "nói rõ phần nào bạn còn làm được và phần nào cần nghỉ",
    ),
    "wands-10": (
        "đang ôm nhiều trách nhiệm hơn mình xử lý nổi",
        "coi việc nhờ giúp là một thất bại",
        "chọn một việc để giao lại hoặc thương lượng thời hạn",
    ),
    "wands-page": (
        "tò mò và muốn thử một ý tưởng mới",
        "nói về ý tưởng nhiều hơn thời gian dành để thử",
        "làm một bản thử nhỏ trước khi kể thêm về kế hoạch",
    ),
    "wands-knight": (
        "muốn hành động nhanh khi đang rất hào hứng",
        "đẩy mọi chuyện đi quá nhanh khiến người khác chưa theo kịp",
        "hỏi người cùng làm có đồng ý với bước tiếp theo không",
    ),
    "wands-queen": (
        "muốn thể hiện điều mình thích một cách tự tin",
        "so mình với người nổi bật hơn rồi thu mình lại",
        "chia sẻ một ý tưởng theo cách của bạn mà không bắt chước ai",
    ),
    "wands-king": (
        "có hướng đi rõ và muốn đưa mọi người cùng tiến tới",
        "chốt thay người khác vì nghĩ mình biết tốt hơn",
        "nói mục tiêu rồi hỏi mỗi người có thể đảm nhận phần nào",
    ),
    "swords-ace": (
        "nhìn rõ một điều sau khi hỏi đúng câu hỏi",
        "nói quá sắc khiến ý đúng cũng khó được nghe",
        "nói thẳng một ý và bỏ lời châm chọc khỏi câu đó",
    ),
    "swords-2": (
        "đang kẹt giữa hai lựa chọn và chưa muốn quyết định",
        "tránh tìm hiểu vì sợ câu trả lời không như mình muốn",
        "viết ra thông tin còn thiếu để so hai lựa chọn",
    ),
    "swords-3": (
        "một lời nói hoặc sự thật làm mình buồn",
        "biến một câu nói đau thành phán xét về cả bản thân",
        "viết điều đã được nói, rồi tách phần bạn đang tự trách",
    ),
    "swords-4": (
        "cần nghỉ đầu óc sau nhiều suy nghĩ hoặc tranh luận",
        "cố xử lý tiếp khi mình đã quá mệt để nghe rõ",
        "hẹn một giờ nói tiếp và nghỉ khỏi cuộc tranh luận trước",
    ),
    "swords-5": (
        "một cuộc tranh luận có thể để lại khó chịu dù có người thắng",
        "nói cho hả giận rồi làm chuyện khó sửa hơn",
        "bỏ câu công kích và nói điều bạn muốn giải quyết",
    ),
    "swords-6": (
        "muốn bớt căng thẳng và xử lý chuyện theo cách bình tĩnh hơn",
        "tưởng đổi chỗ là vấn đề tự biến mất",
        "chọn một chuyện cần giải quyết khi cả hai đã bình tĩnh",
    ),
    "swords-7": (
        "cần xem lại điều mình đang giấu hoặc tránh nói rõ",
        "giữ im lặng để có lợi thế thay vì thống nhất với người khác",
        "nói rõ một điều người cùng làm cần biết để quyết định",
    ),
    "swords-8": (
        "cảm thấy không có lựa chọn dù vẫn còn một phần mình quyết được",
        "coi mọi nỗi sợ là lý do mình không thể làm gì",
        "kể tên một việc bạn tự quyết được mà không cần ai cho phép",
    ),
    "swords-9": (
        "lo lắng khiến một chuyện chạy đi chạy lại trong đầu",
        "coi kịch bản đáng sợ nhất là chuyện chắc sẽ xảy ra",
        "viết một điều đã biết và một điều bạn còn đang lo",
    ),
    "swords-10": (
        "một việc đã kết thúc hoặc không còn tiếp tục như trước",
        "cố kéo dài chỉ vì đã bỏ quá nhiều công sức",
        "nói rõ điều đã kết thúc và việc thực tế cần thu xếp",
    ),
    "swords-page": (
        "muốn hỏi và tìm hiểu trước khi tin một điều",
        "tra hỏi liên tục khiến người khác cảm thấy bị nghi ngờ",
        "hỏi một câu cụ thể và nghe hết câu trả lời",
    ),
    "swords-knight": (
        "muốn giải quyết nhanh bằng một câu nói thẳng",
        "nói trước khi hiểu hết chuyện của người kia",
        "hỏi lại xem bạn hiểu đúng chưa rồi mới phản hồi",
    ),
    "swords-queen": (
        "muốn nói rõ giới hạn mà không vòng vo",
        "dùng sự lạnh lùng thay cho một lời giải thích rõ",
        "nói điều bạn không nhận lời và lý do ngắn gọn",
    ),
    "swords-king": (
        "cần quyết định dựa trên thông tin thay vì tranh cãi",
        "chỉ nghe lý lẽ mà bỏ qua điều người khác đang lo",
        "nêu thông tin bạn dựa vào rồi hỏi còn điều gì chưa được tính đến",
    ),
    "pentacles-ace": (
        "có một cơ hội cần thời gian và công sức để thành việc thật",
        "coi lời đề nghị ban đầu là một kết quả đã chắc",
        "hỏi rõ việc cần làm và thời gian cần bỏ ra",
    ),
    "pentacles-2": (
        "đang chia thời gian giữa nhiều việc cùng cần mình",
        "đổi ưu tiên liên tục đến mức việc nào cũng dở dang",
        "chốt việc cần làm trước và báo lại việc phải chờ",
    ),
    "pentacles-3": (
        "làm cùng người khác sẽ tốt hơn nếu rõ phần của từng người",
        "nghĩ người khác tự biết tiêu chuẩn bạn muốn",
        "thống nhất ai làm gì và thế nào được coi là xong",
    ),
    "pentacles-4": (
        "muốn giữ chặt thời gian hoặc những gì mình đang có",
        "sợ mất đến mức không cho phép thay đổi dù nhỏ",
        "xác định một điều cần giữ và một điều có thể linh hoạt",
    ),
    "pentacles-5": (
        "thấy mình thiếu sự hỗ trợ khi đang gặp khó",
        "ngại nói mình cần gì rồi chịu một mình",
        "nhờ một người đáng tin giúp đúng một việc cụ thể",
    ),
    "pentacles-6": (
        "cần nhìn xem hai bên đang cho và nhận có cân bằng không",
        "giúp rồi âm thầm mong người kia phải đáp lại",
        "nói rõ bạn giúp được gì và có mong điều gì đáp lại không",
    ),
    "pentacles-7": (
        "đã bỏ công và cần xem cách làm có đáng tiếp tục không",
        "chỉ vì đã làm lâu mà không dám đổi cách",
        "so điều đã bỏ ra với kết quả thật trước khi nhận thêm việc",
    ),
    "pentacles-8": (
        "tiến bộ nhờ làm một kỹ năng đều đặn",
        "sửa tiểu tiết mãi rồi quên mục đích của việc",
        "chọn một kỹ năng để luyện và một mốc đủ tốt để dừng",
    ),
    "pentacles-9": (
        "muốn tự chủ và tận hưởng điều mình đã làm được",
        "coi tự lập là không bao giờ được nhờ ai",
        "giữ một việc bạn tự làm và cho phép mình nhờ giúp việc khác",
    ),
    "pentacles-10": (
        "muốn xây điều ổn định có thể chia sẻ với người thân",
        "làm theo kỳ vọng gia đình dù chưa nói điều mình muốn",
        "hỏi rõ trách nhiệm chung và nói phần bạn đồng ý nhận",
    ),
    "pentacles-page": (
        "muốn học một điều có thể dùng được trong thực tế",
        "chuẩn bị dụng cụ mãi mà chưa bắt đầu học",
        "làm một bài thử ngắn với những gì bạn đang có",
    ),
    "pentacles-knight": (
        "làm chậm nhưng đều và giữ được điều đã hứa",
        "giữ cách cũ đến mức không thử cách tốt hơn",
        "giữ việc đang hiệu quả và thử đổi một bước nhỏ",
    ),
    "pentacles-queen": (
        "quan tâm bằng những việc thiết thực hằng ngày",
        "chăm mọi người rồi bỏ qua việc ăn nghỉ của mình",
        "xếp một việc chăm mình vào lịch trước khi nhận thêm việc",
    ),
    "pentacles-king": (
        "muốn dùng kinh nghiệm để làm một việc ổn định và lâu dài",
        "dùng quyền quyết định để bắt người khác làm theo",
        "thống nhất trách nhiệm và quyền lựa chọn của từng người",
    ),
}
