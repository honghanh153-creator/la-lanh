"""Original relationship meanings: possibilities, not facts about another person.

The selected card stays unchanged. This bank translates its symbolism into
time together, conversations, care and boundaries instead of workplace copy.
"""

RELATIONSHIP_READINGS: dict[str, tuple[str, str, str]] = {
    "major-fool": (
        "muốn thử làm quen mà chưa biết chuyện sẽ đi đến đâu",
        "hào hứng quá nên bỏ qua điều mình chưa biết về người kia",
        "rủ một cuộc gặp đơn giản, chưa hứa chuyện lâu dài",
    ),
    "major-magician": (
        "có thể chủ động nói rõ điều mình muốn trong mối quan hệ",
        "cố nói cho hay để được thích thay vì nói thật",
        "nói một điều bạn muốn và hỏi người kia có muốn điều tương tự không",
    ),
    "major-high-priestess": (
        "có điều bạn đang cảm thấy nhưng chưa nói thành lời",
        "coi linh cảm là bằng chứng về suy nghĩ của người kia",
        "ghi lại điều bạn đã thấy rồi hỏi về chi tiết chưa rõ",
    ),
    "major-empress": (
        "muốn được quan tâm bằng những việc nhỏ, đều đặn",
        "chăm người kia nhiều đến mức quên nhu cầu của mình",
        "nói với người kia một việc nhỏ khiến bạn thấy được quan tâm",
    ),
    "major-emperor": (
        "muốn hai người có lời hẹn và giới hạn rõ ràng",
        "muốn mọi chuyện theo ý mình để bớt lo",
        "đề nghị một thỏa thuận rồi để người kia góp ý",
    ),
    "major-hierophant": (
        "cần biết hai người có cùng cách nhìn về sự cam kết không",
        "làm theo kỳ vọng của gia đình hoặc bạn bè dù mình không muốn",
        "hỏi cả hai hiểu thế nào là một mối quan hệ nghiêm túc",
    ),
    "major-lovers": (
        "muốn tình cảm đi cùng những lựa chọn mà mình thấy đúng",
        "coi sự hấp dẫn là bằng chứng rằng hai người hợp mọi mặt",
        "hỏi một điều về cách sống hoặc mong muốn lâu dài của cả hai",
    ),
    "major-chariot": (
        "muốn mối quan hệ tiến thêm một bước thay vì cứ chờ",
        "thúc người kia theo tốc độ mình muốn",
        "nói bước bạn muốn tiến tới và hỏi người kia đã sẵn sàng chưa",
    ),
    "major-strength": (
        "có thể nói điều khó chịu mà không làm người kia tổn thương",
        "cố nhịn hết để giữ hòa khí rồi bực lâu hơn",
        "nói điều khiến bạn khó chịu bằng một câu không công kích",
    ),
    "major-hermit": (
        "cần thời gian riêng để biết mình muốn gì trước khi nhắn lại",
        "im lặng quá lâu mà không nói mình cần nghỉ",
        "báo rằng bạn cần nghĩ thêm và hẹn lúc có thể nói chuyện tiếp",
    ),
    "major-wheel-of-fortune": (
        "nhịp gặp gỡ có thể thay đổi khi lịch và hoàn cảnh thay đổi",
        "coi một lần ít liên lạc là kết luận về cả mối quan hệ",
        "hỏi lịch hiện tại của người kia trước khi đoán lý do ít nhắn",
    ),
    "major-justice": (
        "cần nhìn cả điều mình làm lẫn điều mình mong người kia làm",
        "chỉ kể phần mình thiệt mà bỏ qua trách nhiệm của mình",
        "nêu một thỏa thuận cụ thể mà cả hai đều có thể thực hiện",
    ),
    "major-hanged-man": (
        "có thể hiểu một cuộc cãi nhau khác đi khi nghe hết phía còn lại",
        "chờ người kia tự thay đổi mà không nói điều mình cần",
        "hỏi người kia đã hiểu chuyện đó thế nào rồi nói phần của bạn",
    ),
    "major-death": (
        "một cách cư xử cũ cần dừng lại để hai người nói chuyện khác đi",
        "cố giữ mọi thứ như cũ dù chuyện đó đã làm mình mệt",
        "nêu một cách cư xử bạn không muốn tiếp tục và một cách thay thế",
    ),
    "major-temperance": (
        "hai người cần điều chỉnh để tìm cách liên lạc vừa với cả hai",
        "nhường mãi mà không nói điều mình thật sự muốn",
        "thống nhất một cách liên lạc mà cả hai thấy thoải mái",
    ),
    "major-devil": (
        "sự hấp dẫn hoặc thói quen có thể khiến bạn khó giữ giới hạn",
        "đồng ý điều mình không muốn vì sợ mất người kia",
        "nói rõ một giới hạn bạn cần giữ, dù đang rất thích người kia",
    ),
    "major-tower": (
        "một chuyện bất ngờ có thể buộc bạn nhìn lại điều từng tin về kết nối này",
        "kết luận cả mối quan hệ từ một lần cãi nhau",
        "xác định việc đã xảy ra và điều cần làm rõ trước khi quyết định",
    ),
    "major-star": (
        "muốn tin rằng mình vẫn có thể được lắng nghe sau một lần thất vọng",
        "chỉ hy vọng mọi chuyện tự tốt hơn mà không nói nhu cầu",
        "nói một điều bạn mong hai người làm khác trong lần tới",
    ),
    "major-moon": (
        "chưa rõ người kia muốn gì nên dễ tự nghĩ thêm lý do",
        "coi một tin nhắn ngắn là bằng chứng người kia hết quan tâm",
        "hỏi về điều chưa rõ thay vì kiểm tra bằng cách lạnh nhạt lại",
    ),
    "major-sun": (
        "muốn được nói thật và thoải mái khi ở cạnh người kia",
        "giả vờ vui để tránh nói chuyện đang làm mình khó chịu",
        "nói một điều bạn thích và một điều bạn muốn hai người sửa",
    ),
    "major-judgement": (
        "cần nhìn lại cách hai người từng giải quyết những chuyện tương tự",
        "nhận lời làm lại dù chưa rõ lần này sẽ khác ở đâu",
        "hỏi cả hai có thể làm khác điều gì thay vì chỉ hứa cố gắng",
    ),
    "major-world": (
        "muốn biết hai người đã đi đến đâu và có muốn bước tiếp không",
        "giữ một kết nối chỉ vì đã dành nhiều thời gian cho nó",
        "hỏi rõ cả hai muốn giữ, thay đổi hay khép lại điều gì",
    ),
    "cups-ace": (
        "bắt đầu có cảm tình và muốn cho người kia biết",
        "vội coi rung động ban đầu là một lời hứa",
        "nói một điều bạn thích mà chưa đòi lời cam kết",
    ),
    "cups-2": (
        "muốn việc lắng nghe và đáp lại đến từ cả hai phía",
        "tưởng mình thích thì người kia cũng phải thích",
        "hỏi xem cả hai có muốn tiếp tục tìm hiểu không",
    ),
    "cups-3": (
        "muốn kết nối qua những cuộc gặp vui và bạn bè chung",
        "để ý kiến của bạn bè thay mình quyết định về người kia",
        "dành một cuộc nói chuyện riêng cho điều chưa tiện nói trước nhóm",
    ),
    "cups-4": (
        "chưa thấy hứng thú với cách hai người đang tìm hiểu nhau",
        "nhận lời gặp chỉ vì ngại từ chối",
        "nói rõ bạn chưa muốn nhận lời lúc này",
    ),
    "cups-5": (
        "còn buồn về một việc giữa hai người và khó nhìn ngoài chuyện đó",
        "coi một lần thất vọng là kết luận về mọi lần sau",
        "nói rõ việc làm bạn buồn và điều bạn muốn thay đổi",
    ),
    "cups-6": (
        "nhớ cảm giác thân thuộc từ một người hoặc chuyện cũ",
        "chỉ nhớ phần đẹp rồi bỏ qua lý do chuyện cũ kết thúc",
        "viết cả điều bạn nhớ lẫn điều từng khiến bạn không vui",
    ),
    "cups-7": (
        "có nhiều điều mong từ người kia nhưng chưa biết điều nào thực tế",
        "thích người mình tưởng tượng hơn người mình đang gặp",
        "chọn một mong muốn và hỏi người kia có muốn điều tương tự không",
    ),
    "cups-8": (
        "nhận ra cách hai người đang ở cạnh nhau chưa làm mình hài lòng",
        "rời đi chỉ để tránh một cuộc nói chuyện khó",
        "nói điều bạn đang thiếu trước khi quyết định có tiếp tục không",
    ),
    "cups-9": (
        "biết điều gì khiến mình vui khi ở trong một mối quan hệ",
        "chờ người kia xác nhận rằng nhu cầu của mình là hợp lý",
        "nêu một điều bạn thích mà không bắt người kia phải giống mình",
    ),
    "cups-10": (
        "muốn được là mình và thấy yên tâm khi ở cạnh người kia",
        "giữ hình ảnh hòa thuận dù còn chuyện chưa nói",
        "hỏi cả hai cần điều gì để ở cạnh nhau thoải mái hơn",
    ),
    "cups-page": (
        "muốn nói một lời dễ thương nhưng còn ngại",
        "đọc quá nhiều ý nghĩa vào một lời quan tâm nhỏ",
        "nói điều bạn cảm thấy bằng một câu đơn giản",
    ),
    "cups-knight": (
        "muốn thể hiện tình cảm bằng một lời nói hoặc lời mời",
        "hứa lúc hào hứng rồi không sắp xếp được",
        "chỉ hẹn một việc bạn thật sự có thể làm",
    ),
    "cups-queen": (
        "muốn nghe và hiểu cảm xúc của người kia",
        "nhận luôn trách nhiệm làm người kia vui",
        "hỏi người kia muốn được nghe hay được giúp trước khi làm thay",
    ),
    "cups-king": (
        "muốn nói rõ cảm xúc mà vẫn giữ bình tĩnh",
        "giấu hết cảm xúc để trông như mình vẫn ổn",
        "nói điều bạn đang cảm thấy mà không đổ lỗi cho người kia",
    ),
    "wands-ace": (
        "có hứng chủ động rủ người kia làm một việc mới",
        "đưa nhiều lời hứa ngay lúc mới hào hứng",
        "rủ một việc nhỏ bạn thật sự muốn làm cùng người kia",
    ),
    "wands-2": (
        "muốn tiến thêm nhưng còn cân nhắc có nên chủ động không",
        "nghĩ mãi về lời mời mà chưa gửi",
        "đưa một lời mời cụ thể để người kia có thể nhận hoặc từ chối",
    ),
    "wands-3": (
        "đã chủ động và đang chờ xem người kia có đáp lại không",
        "chỉ chờ phản hồi mà chưa nói rõ bước tiếp theo",
        "nói rõ lời mời của bạn rồi để người kia có thời gian trả lời",
    ),
    "wands-4": (
        "muốn có những cuộc gặp khiến cả hai thoải mái và được chào đón",
        "coi một cuộc gặp vui là dấu hiệu mọi khác biệt đã hết",
        "rủ một cuộc gặp đơn giản rồi hỏi cả hai thấy thế nào",
    ),
    "wands-5": (
        "hai người có thể khác ý mà vẫn cần nghe được nhau",
        "biến một bất đồng nhỏ thành cuộc thi ai đúng",
        "chỉ nói một điểm đang khác ý, không lôi chuyện cũ vào",
    ),
    "wands-6": (
        "muốn công sức mình dành cho kết nối này được nhìn thấy",
        "chờ người kia khen rồi mới thấy việc mình làm có giá trị",
        "nói một việc bạn đã cố gắng và cách bạn muốn được ghi nhận",
    ),
    "wands-7": (
        "cần giữ điều mình muốn dù người kia không đồng ý ngay",
        "phản ứng như bị tấn công trước cả khi nghe hết lời",
        "nói giới hạn của mình rồi nghe người kia giải thích",
    ),
    "wands-8": (
        "muốn cuộc trò chuyện tiến nhanh và có câu trả lời rõ",
        "nhắn dồn để ép một câu trả lời ngay",
        "gửi một câu hỏi rõ rồi chờ câu trả lời trước khi nhắn tiếp",
    ),
    "wands-9": (
        "muốn bảo vệ mình sau một trải nghiệm không vui",
        "coi người mới gặp như người từng làm mình thất vọng",
        "nói điều khiến bạn dè chừng mà không quy lỗi cho người kia",
    ),
    "wands-10": (
        "có thể đang nhận quá nhiều phần giữ liên lạc và sắp xếp gặp gỡ",
        "làm hết rồi mong người kia tự biết mình đang mệt",
        "hỏi người kia nhận một phần sắp xếp cụ thể trong lần tới",
    ),
    "wands-page": (
        "muốn làm quen và xem hai người có vui khi trò chuyện không",
        "coi sự tò mò lúc đầu là tình cảm đã chắc",
        "hỏi một điều bạn thật sự tò mò về người kia",
    ),
    "wands-knight": (
        "muốn tiến nhanh vì đang thấy người kia rất cuốn hút",
        "hứa nhiều hơn mức mình có thể duy trì",
        "chọn một lời hẹn vừa với lịch và mong muốn thật của bạn",
    ),
    "wands-queen": (
        "muốn tự tin thể hiện điều mình thích mà không phải diễn khác đi",
        "cố tỏ ra thú vị liên tục để giữ sự chú ý",
        "rủ người kia một việc bạn vốn thích, không cần cố gây ấn tượng",
    ),
    "wands-king": (
        "muốn chủ động nói hướng mình muốn hai người tiến tới",
        "quyết định thay cả hai vì nghĩ mình biết điều tốt nhất",
        "nói mong muốn của bạn rồi hỏi người kia có cùng mong muốn không",
    ),
    "swords-ace": (
        "cần một câu nói rõ để hai người bớt hiểu lầm",
        "nói đúng ý nhưng dùng lời khiến người kia khó nghe",
        "nói một việc cụ thể và điều bạn muốn hai người làm khác",
    ),
    "swords-2": (
        "chưa biết nên nói tiếp hay dừng để nghĩ thêm",
        "né câu trả lời để khỏi làm người kia buồn",
        "nói rõ phần bạn chưa quyết định được và điều cần biết thêm",
    ),
    "swords-3": (
        "có điều khiến bạn buồn cần được nói thẳng trong cuộc trò chuyện",
        "dùng lời nặng để người kia phải đau như mình",
        "kể một việc khiến bạn buồn mà không gán ý đồ cho người kia",
    ),
    "swords-4": (
        "cần nghỉ khỏi cuộc cãi nhau trước khi có thể nói tiếp",
        "biến việc cần nghỉ thành im lặng để trừng phạt người kia",
        "báo rằng bạn cần nghỉ và hẹn một lúc cụ thể để nói tiếp",
    ),
    "swords-5": (
        "cần xem cuộc tranh luận đang giúp hiểu nhau hay chỉ để thắng",
        "cố có lời cuối dù biết người kia đang tổn thương",
        "dừng tranh thắng rồi hỏi việc nào cả hai cần giải quyết",
    ),
    "swords-6": (
        "muốn hai người thoát khỏi cách cãi nhau đã làm cả hai mệt",
        "đổi chủ đề mà chưa giải quyết điều gây khó chịu",
        "thống nhất một cách nói khác cho đúng chuyện đang mắc",
    ),
    "swords-7": (
        "có điều bạn đang tránh nói thật với người kia",
        "giữ thông tin để kiểm soát câu trả lời của người kia",
        "nói một điều bạn đã tránh nhắc đến nếu thấy an toàn để nói",
    ),
    "swords-8": (
        "sợ phản ứng của người kia đến mức thấy mình không có lựa chọn",
        "tự quyết rằng mình không được nói trước khi thử hỏi",
        "viết một câu bạn muốn nói và chọn lúc bạn thấy an toàn",
    ),
    "swords-9": (
        "lo về kết nối này đến mức nghĩ đi nghĩ lại một chi tiết",
        "coi tình huống mình sợ nhất là điều chắc sẽ xảy ra",
        "ghi điều đã biết và điều cần hỏi, không đọc lại tin nhắn liên tục",
    ),
    "swords-10": (
        "một chuyện giữa hai người có thể đã làm bạn quá mệt",
        "cố kéo dài cuộc tranh luận chỉ để có một lời giải thích trọn vẹn",
        "dừng cuộc nói chuyện đang làm bạn quá sức và tìm người tin cậy để kể",
    ),
    "swords-page": (
        "muốn biết thêm trước khi tin vào điều người kia nói",
        "hỏi dồn như tra xét thay vì tìm hiểu",
        "hỏi một chi tiết chưa rõ, không kiểm tra điện thoại hay tài khoản của ai",
    ),
    "swords-knight": (
        "muốn nói ngay điều mình thấy không đúng",
        "phản bác quá nhanh mà chưa nghe hết lời",
        "nghe người kia nói hết rồi hỏi lại đúng một điểm",
    ),
    "swords-queen": (
        "muốn nói thẳng điều mình cần và không muốn trong mối quan hệ",
        "nói sắc quá khiến điều mình muốn bị che bởi giọng điệu",
        "nói rõ giới hạn bằng câu về mình, không chê con người của họ",
    ),
    "swords-king": (
        "cần thống nhất điều cụ thể thay vì tranh luận theo cảm xúc lúc đó",
        "đòi người kia phải lý trí rồi bỏ qua điều họ đang buồn",
        "nhắc lại điều đã nghe trước khi đề nghị một thỏa thuận",
    ),
    "pentacles-ace": (
        "muốn biến lời hẹn thành thời gian gặp nhau thật",
        "coi một lời mời ban đầu là cam kết đã chắc",
        "đề nghị một ngày gặp vừa với lịch của cả hai",
    ),
    "pentacles-2": (
        "cần sắp xếp thời gian cho người kia mà vẫn giữ việc riêng",
        "nhận mọi lời hẹn rồi thay đổi vào phút cuối",
        "nói một khoảng thời gian bạn thật sự có thể dành cho cuộc gặp",
    ),
    "pentacles-3": (
        "muốn hai người cùng góp sức vào chuyện đã thống nhất",
        "nghĩ người kia tự biết phần cần làm",
        "hỏi cả hai sẽ làm gì để buổi gặp hoặc kế hoạch chung diễn ra",
    ),
    "pentacles-4": (
        "muốn biết mối quan hệ có ổn định trước khi thay đổi cách gần gũi",
        "giữ người kia quá chặt vì sợ kết nối thay đổi",
        "nói điều khiến bạn lo, không yêu cầu người kia báo cáo mọi việc",
    ),
    "pentacles-5": (
        "có thể thấy mình bị bỏ ngoài một chuyện cần có sự quan tâm",
        "ngại nói mình cần giúp rồi kết luận không ai quan tâm",
        "nói một điều bạn cần được hỗ trợ và hỏi người kia có thể giúp không",
    ),
    "pentacles-6": (
        "cần nhìn việc cho và nhận có thoải mái với cả hai không",
        "cho đi rồi mong người kia trả lại theo cách chưa nói rõ",
        "nói rõ hai phía có thể dành thời gian và quan tâm cho nhau thế nào",
    ),
    "pentacles-7": (
        "cần xem công sức dành cho kết nối này có đem lại điều mình muốn không",
        "tiếp tục chỉ vì đã dành nhiều thời gian chờ đợi",
        "nhìn một thay đổi thật gần đây trước khi quyết định chờ thêm",
    ),
    "pentacles-8": (
        "muốn cải thiện cách hai người nói chuyện qua những việc nhỏ lặp lại",
        "cố sửa bản thân một mình để mối quan hệ tốt lên",
        "rủ người kia cùng thử một thay đổi trong cách nói chuyện",
    ),
    "pentacles-9": (
        "muốn gần gũi mà vẫn có thời gian và cuộc sống riêng",
        "tỏ ra không cần ai dù thật ra muốn được quan tâm",
        "nói lúc nào bạn muốn ở riêng và lúc nào bạn muốn gặp người kia",
    ),
    "pentacles-10": (
        "muốn biết chuyện gia đình và kế hoạch lâu dài ảnh hưởng hai người ra sao",
        "coi việc được gia đình chấp nhận là đủ để hai người hợp nhau",
        "hỏi một điều về kế hoạch lâu dài mà cả hai cần thống nhất",
    ),
    "pentacles-page": (
        "muốn tìm hiểu người kia qua việc họ làm chứ không chỉ lời nói",
        "xem một cử chỉ nhỏ như bằng chứng cho toàn bộ mối quan hệ",
        "hẹn một việc đơn giản và nhìn cách cả hai giữ lời",
    ),
    "pentacles-knight": (
        "muốn sự quan tâm đều đặn và có thể tin cậy",
        "giữ một thói quen liên lạc dù nó không còn hợp với cả hai",
        "hỏi cách gặp gỡ hoặc nhắn tin hiện tại có còn thoải mái không",
    ),
    "pentacles-queen": (
        "muốn thể hiện sự quan tâm bằng việc chăm sóc thiết thực",
        "làm hết cho người kia rồi quên mình cũng cần nghỉ",
        "chỉ nhận một việc bạn giúp được và nói rõ phần bạn không thể nhận",
    ),
    "pentacles-king": (
        "muốn lời hứa được thể hiện qua việc làm ổn định",
        "dùng tiền hoặc sự giúp đỡ để có quyền quyết định thay người kia",
        "thống nhất một việc cả hai có thể giữ lời mà không ai mắc nợ ai",
    ),
}

RELATIONSHIP_EXAMPLES: dict[str, str] = {
    "major-fool": "Bạn muốn rủ người mới quen đi chơi nhưng chưa biết họ có muốn không.",
    "major-magician": "Bạn soạn một lời mời rất khéo nhưng chưa nói mình thật sự muốn gì.",
    "major-high-priestess": "Một câu trả lời hơi lạ khiến bạn đoán có điều đang bị giấu.",
    "major-empress": "Bạn nhớ người kia thích ăn gì nhưng chưa kể mình thích được quan tâm ra sao.",
    "major-emperor": (
        "Bạn muốn hai người báo trước khi đổi lịch, còn chuyện này chưa được thống nhất."
    ),
    "major-hierophant": "Bạn bè bảo phải nhắn ít mới được thích, dù bạn muốn nói chuyện tự nhiên.",
    "major-lovers": "Bạn thích một người nhưng hai bên muốn những kiểu quan hệ khác nhau.",
    "major-chariot": "Bạn muốn gặp thường xuyên hơn nhưng chưa hỏi lịch người kia.",
    "major-strength": "Bạn đang bực, đã soạn một câu gắt nhưng chưa gửi.",
    "major-hermit": "Bạn chưa trả lời tin nhắn vì cần nghĩ thêm nhưng chưa báo người kia.",
    "major-wheel-of-fortune": "Người kia nhắn ít trong tuần bận hơn, còn bạn chưa hỏi lịch của họ.",
    "major-justice": "Bạn trách người kia quên một lời hẹn mà chưa nhắc phần mình cũng đổi lịch.",
    "major-hanged-man": "Hai người cãi về cùng một chuyện nhưng chưa kể mỗi bên đã hiểu thế nào.",
    "major-death": "Bạn vẫn nhắn theo thói quen cũ dù cả hai đã nói muốn đổi cách liên lạc.",
    "major-temperance": "Bạn thích nhắn mỗi ngày, người kia thích gọi vài lần mỗi tuần.",
    "major-devil": "Bạn nhận một lời hẹn mình không muốn chỉ vì sợ bị người kia bỏ quên.",
    "major-tower": "Một thông tin mới khiến bạn phải hỏi lại điều hai người từng thống nhất.",
    "major-star": "Sau lần nói chuyện không vui, bạn vẫn muốn thử một cách mở lời khác.",
    "major-moon": "Tin nhắn ngắn hơn thường lệ làm bạn lo dù chưa biết người kia đang bận gì.",
    "major-sun": "Buổi gặp trông vui nhưng bạn còn một chuyện khó chịu chưa nói.",
    "major-judgement": "Hai người muốn làm lại nhưng vẫn dùng đúng cách cãi nhau lần trước.",
    "major-world": (
        "Bạn muốn hỏi hai người đang ở đâu trong mối quan hệ sau một thời gian tìm hiểu."
    ),
    "cups-ace": "Bạn vui khi gặp một người mới và muốn nói điều đó mà chưa hứa gì xa.",
    "cups-2": "Cả hai cùng hỏi han và nhớ chuyện người kia kể, không chỉ một bên bắt chuyện.",
    "cups-3": "Bạn vui với nhóm bạn chung nhưng muốn nói một chuyện riêng với người kia.",
    "cups-4": "Bạn chưa muốn nhận lời đi chơi nhưng ngại vì người rủ rất nhiệt tình.",
    "cups-5": "Một buổi hẹn hụt khiến bạn nghĩ mọi lần gặp sau cũng sẽ như vậy.",
    "cups-6": "Bạn nhớ người cũ qua một bài hát rồi quên những lần hai người không hiểu nhau.",
    "cups-7": "Bạn tưởng tượng nhiều về tương lai với một người mình mới gặp vài lần.",
    "cups-8": "Hai người vẫn gặp đều nhưng bạn thấy có điều mình cần chưa được nói ra.",
    "cups-9": "Bạn muốn một buổi tối riêng nhưng ngại người kia nghĩ mình bớt thích họ.",
    "cups-10": "Hai người trông hòa thuận nhưng chưa nói về một thói quen sống khiến bạn khó chịu.",
    "cups-page": "Bạn sửa một lời quan tâm nhiều lần vì sợ người kia nghĩ mình thích quá.",
    "cups-knight": "Bạn hẹn nhiều cuộc gặp lúc hào hứng rồi nhận ra lịch mình không đủ.",
    "cups-queen": "Người kia kể chuyện buồn, bạn tìm cách giúp ngay mà chưa hỏi họ muốn gì.",
    "cups-king": "Bạn nói mình không sao dù một câu người kia nói đã khiến bạn buồn.",
    "wands-ace": "Bạn muốn rủ người kia thử một hoạt động mới và đang rất hào hứng.",
    "wands-2": "Bạn đã nghĩ ra lời mời nhưng cứ chờ có dấu hiệu đồng ý rồi mới dám hỏi.",
    "wands-3": "Bạn đã đưa lời mời, đang chờ trả lời và chưa biết lúc nào nên hỏi lại.",
    "wands-4": "Một buổi gặp rất vui khiến bạn quên chuyện cả hai còn cần làm rõ.",
    "wands-5": "Hai người nói cùng lúc để bảo vệ ý mình nên chưa ai nghe hết phía còn lại.",
    "wands-6": "Bạn sắp xếp buổi gặp nhưng buồn vì công sức ấy chưa được nhắc tới.",
    "wands-7": "Người kia hỏi lý do, bạn nghe như họ đang phủ nhận lựa chọn của mình.",
    "wands-8": "Bạn định gửi thêm nhiều tin trong khi câu hỏi trước chưa được trả lời.",
    "wands-9": "Một người mới hỏi chuyện riêng và bạn nhớ ngay lần từng bị làm thất vọng.",
    "wands-10": "Bạn luôn chọn chỗ, đặt lịch và nhắc cuộc hẹn trong khi cũng đang rất bận.",
    "wands-page": "Bạn tò mò về một sở thích của người kia và muốn có cớ để bắt chuyện.",
    "wands-knight": (
        "Bạn muốn gặp liên tục ngay lúc mới thích mà chưa xem mình giữ được lịch không."
    ),
    "wands-queen": "Bạn muốn rủ việc mình thích nhưng sợ nó không đủ thú vị với người kia.",
    "wands-king": (
        "Bạn đã nghĩ đến bước tiếp theo nhưng chưa hỏi người kia có cùng mong muốn không."
    ),
    "swords-ace": "Bạn hỏi thẳng một chi tiết và nhận ra hiểu lầm đến từ việc thiếu thông tin.",
    "swords-2": "Bạn chưa muốn nhận lời nhưng cứ để câu hỏi của người kia không có trả lời.",
    "swords-3": "Một câu nói khiến bạn buồn nhưng bạn chưa kể rõ câu nào làm mình đau.",
    "swords-4": "Hai người càng nói càng bực mà chưa ai đề nghị nghỉ rồi quay lại.",
    "swords-5": "Bạn nghĩ ra câu đáp có thể thắng cãi nhau nhưng biết nó sẽ làm người kia đau.",
    "swords-6": "Bạn muốn đổi cách nói để bớt căng nhưng vẫn quay lại cách trách nhau cũ.",
    "swords-7": "Bạn tránh kể một chi tiết quan trọng vì ngại cuộc nói chuyện sẽ khó hơn.",
    "swords-8": "Bạn nghĩ mình không thể từ chối lời hẹn dù chưa từng nói lịch mình không hợp.",
    "swords-9": "Bạn đọc lại một tin nhắn tối muộn và nghĩ ra thêm nhiều khả năng đáng lo.",
    "swords-10": "Cuộc cãi nhau đã làm bạn quá mệt nhưng bạn vẫn cố để có lời giải thích cuối.",
    "swords-page": (
        "Bạn hỏi liên tiếp nhiều chi tiết khiến cuộc trò chuyện giống một buổi kiểm tra."
    ),
    "swords-knight": "Bạn phản bác một câu trước khi người kia nói hết ý.",
    "swords-queen": "Bạn biết mình không muốn bị trêu về một chuyện nhưng chưa nói giới hạn ấy.",
    "swords-king": "Hai người còn cãi về ai đúng mà chưa thống nhất cách xử lý lần sau.",
    "pentacles-ace": "Bạn nhận một lời mời gặp nhưng hai người chưa chọn ngày và chỗ cụ thể.",
    "pentacles-2": "Bạn nhận nhiều lời hẹn rồi phải dời buổi gặp vì lịch đã kín.",
    "pentacles-3": "Hai người cùng muốn đi chơi nhưng chưa thống nhất ai đặt chỗ và đi lúc nào.",
    "pentacles-4": "Bạn muốn người kia kể mọi việc trong ngày để mình bớt lo.",
    "pentacles-5": "Bạn muốn được hỏi han lúc mệt nhưng ngại nói mình cần điều đó.",
    "pentacles-6": "Bạn thường giúp và sắp xếp rồi buồn khi không được quan tâm tương tự.",
    "pentacles-7": "Bạn chờ người kia thay đổi đã lâu nhưng chưa thấy việc nào thật sự khác.",
    "pentacles-8": "Bạn cố sửa cách nhắn của mình nhưng hai người chưa cùng bàn về hiểu lầm.",
    "pentacles-9": "Bạn muốn một tối cho sở thích riêng mà ngại người kia nghĩ mình xa cách.",
    "pentacles-10": "Hai người muốn tính lâu dài nhưng chưa nói về gia đình và cách sống.",
    "pentacles-page": "Một lời hẹn nhỏ giúp bạn nhìn cách cả hai giữ điều đã nói.",
    "pentacles-knight": "Hai người vẫn nhắn đúng giờ cũ nhưng cách đó đang không hợp lịch mới.",
    "pentacles-queen": "Bạn lo đủ đồ cho buổi gặp rồi phải cắt phần nghỉ của mình.",
    "pentacles-king": "Bạn muốn giúp một việc lớn nhưng chưa nói mức giúp khiến mình thoải mái.",
}
