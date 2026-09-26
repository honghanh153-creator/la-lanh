import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BookmarkSimple,
  CalendarBlank,
  Check,
  CheckCircle,
  Clock,
  EnvelopeSimple,
  Eye,
  EyeSlash,
  House,
  Info,
  LockKey,
  MagnifyingGlass,
  MapPin,
  Moon,
  PaperPlaneTilt,
  Planet,
  ShareNetwork,
  ShieldCheck,
  Sparkle,
  StarFour,
  User,
  WarningCircle,
  X,
} from "@phosphor-icons/react";

const moods = [
  { id: "Rực", glyph: "✹" },
  { id: "Chill", glyph: "≋" },
  { id: "Đuối", glyph: "▭" },
  { id: "Căng", glyph: "ϟ" },
  { id: "Lạc trôi", glyph: "◉" },
];

const screens = [
  "welcome",
  "consent",
  "auth",
  "otp",
  "birth",
  "loading",
  "profile",
  "card",
  "home",
  "share",
  "birthTime",
  "moonLoading",
  "moonReveal",
  "saved",
  "profileSettings",
];

function Brand({ compact = false }) {
  return (
    <div className={`brand ${compact ? "brand--compact" : ""}`}>
      <span>Lá Lành</span><sup>*</sup>
    </div>
  );
}

function Progress({ value }) {
  return (
    <div className="progress" aria-label={`Tiến độ ${value}%`}>
      <span style={{ width: `${value}%` }} />
    </div>
  );
}

function TopBar({ onBack, action, compact = true }) {
  return (
    <header className="topbar">
      {onBack ? (
        <button className="icon-button" onClick={onBack} aria-label="Quay lại">
          <ArrowLeft size={22} weight="bold" />
        </button>
      ) : <Brand compact={compact} />}
      {action || <span />}
    </header>
  );
}

function PrimaryButton({ children, onClick, disabled = false, icon, className = "" }) {
  return (
    <button className={`button button--primary ${className}`} onClick={onClick} disabled={disabled}>
      {icon}{children}<ArrowRight size={20} weight="bold" />
    </button>
  );
}

function SecondaryButton({ children, onClick, icon, className = "" }) {
  return (
    <button className={`button button--secondary ${className}`} onClick={onClick}>
      {icon}{children}
    </button>
  );
}

function Celestial({ className = "" }) {
  return <img className={`celestial ${className}`} src="/celestial.png" alt="" />;
}

function Welcome({ next }) {
  const [slide, setSlide] = useState(0);
  const items = [
    {
      eyebrow: "Không phải horoscope chung chung",
      title: <>Một lời nhắc <em>đúng lúc.</em></>,
      body: "Lá Lành đọc chuyển động thật của bầu trời và gửi bạn một note nhỏ mỗi ngày.",
    },
    {
      eyebrow: "Bắt đầu thật nhẹ",
      title: <>Chỉ cần ngày sinh. <em>Thế là đủ.</em></>,
      body: "Giờ và nơi sinh có thể thêm sau, khi bạn muốn lời nhắn chạm sâu hơn.",
    },
  ];
  const item = items[slide];
  return (
    <section className="screen screen--welcome">
      <div className="welcome-header"><Brand /><span className="mini-star">✦</span></div>
      <Celestial className="celestial--welcome" />
      <div className="welcome-copy">
        <p className="eyebrow">{item.eyebrow}</p>
        <h1>{item.title}</h1>
        <p>{item.body}</p>
      </div>
      <div className="welcome-footer">
        <div className="dots"><i className={slide === 0 ? "active" : ""}/><i className={slide === 1 ? "active" : ""}/></div>
        <PrimaryButton onClick={() => slide === 0 ? setSlide(1) : next()}>
          {slide === 0 ? "Tiếp tục" : "Bắt đầu"}
        </PrimaryButton>
        {slide === 0 && <button className="text-button" onClick={next}>Bỏ qua giới thiệu</button>}
      </div>
    </section>
  );
}

function Consent({ next, back }) {
  const [open, setOpen] = useState(false);
  return (
    <section className="screen form-screen">
      <TopBar onBack={back} />
      <Progress value={18} />
      <div className="form-hero">
        <span className="round-icon"><ShieldCheck size={34} weight="duotone" /></span>
        <p className="eyebrow">Trước khi bắt đầu</p>
        <h1>Dữ liệu của bạn vẫn là <span>của bạn.</span></h1>
        <p>Lá Lành cần ngày sinh để tính hồ sơ chiêm tinh. Bạn luôn có thể xem, sửa hoặc xóa dữ liệu bất cứ lúc nào.</p>
      </div>
      <div className="clean-list">
        <div><LockKey size={23}/><span><b>Được mã hóa</b><small>Ngày sinh và tài khoản được lưu an toàn.</small></span></div>
        <div><Eye size={23}/><span><b>Không bán dữ liệu</b><small>Không dùng thông tin cá nhân cho quảng cáo.</small></span></div>
        <div><X size={23}/><span><b>Xóa bất cứ lúc nào</b><small>Bạn kiểm soát toàn bộ dữ liệu đã cung cấp.</small></span></div>
      </div>
      <button className="inline-link" onClick={() => setOpen(true)}>Đọc cách Lá Lành dùng dữ liệu <ArrowRight size={16}/></button>
      <div className="sticky-actions">
        <PrimaryButton onClick={next}>Đồng ý & tiếp tục</PrimaryButton>
      </div>
      {open && (
        <div className="sheet-backdrop" onClick={() => setOpen(false)}>
          <div className="bottom-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="sheet-handle" />
            <h2>Quyền riêng tư, nói dễ hiểu</h2>
            <p>Ngày sinh giúp tính Sun sign. Nếu sau này bạn thêm giờ và nơi sinh, Lá Lành mới tính Moon sign và các lớp sâu hơn.</p>
            <p>Nội dung bạn chia sẻ mặc định không có tên thật. Bạn có thể xóa riêng dữ liệu sinh hoặc toàn bộ tài khoản.</p>
            <PrimaryButton onClick={() => setOpen(false)}>Mình hiểu rồi</PrimaryButton>
          </div>
        </div>
      )}
    </section>
  );
}

function Auth({ next, back }) {
  const [mode, setMode] = useState("phone");
  const [value, setValue] = useState("");
  return (
    <section className="screen form-screen">
      <TopBar onBack={back} />
      <Progress value={32} />
      <div className="form-hero">
        <p className="eyebrow">Giữ note của bạn ở một nơi</p>
        <h1>Bạn muốn nhận mã bằng đâu?</h1>
        <p>Chỉ cần một cách đăng nhập. Không mật khẩu, không phiền.</p>
      </div>
      <div className="segmented">
        <button className={mode === "phone" ? "active" : ""} onClick={() => setMode("phone")}>Số điện thoại</button>
        <button className={mode === "email" ? "active" : ""} onClick={() => setMode("email")}>Email</button>
      </div>
      <label className="field">
        <span>{mode === "phone" ? "Số điện thoại" : "Email"}</span>
        <div>{mode === "phone" && <b>+84</b>}<input autoFocus value={value} onChange={(e) => setValue(e.target.value)} placeholder={mode === "phone" ? "912 345 678" : "an@email.com"} /></div>
      </label>
      <p className="field-note"><Info size={16}/> Chúng mình chỉ dùng thông tin này để xác thực tài khoản.</p>
      <div className="sticky-actions">
        <PrimaryButton disabled={value.length < 5} onClick={next}>Gửi mã xác thực</PrimaryButton>
      </div>
    </section>
  );
}

function OTP({ next, back }) {
  const [code, setCode] = useState("");
  return (
    <section className="screen form-screen">
      <TopBar onBack={back} />
      <Progress value={44} />
      <div className="form-hero">
        <span className="round-icon"><EnvelopeSimple size={32}/></span>
        <p className="eyebrow">Mã đã được gửi</p>
        <h1>Nhập 6 con số vừa ghé qua.</h1>
        <p>Đã gửi tới ••• ••• 678. Mã có hiệu lực trong 05:00.</p>
      </div>
      <input className="otp-input" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))} inputMode="numeric" placeholder="••••••" autoFocus />
      <button className="inline-link centered">Chưa nhận được mã? Gửi lại sau 00:32</button>
      <div className="sticky-actions">
        <PrimaryButton disabled={code.length !== 6} onClick={next}>Xác nhận</PrimaryButton>
      </div>
    </section>
  );
}

function BirthDate({ next, back }) {
  const [date, setDate] = useState("2001-08-14");
  const [error, setError] = useState("");
  const submit = () => {
    const year = Number(date.slice(0, 4));
    if (!date || year > 2013 || year < 1920) setError("Ngày này có vẻ chưa đúng. Thử kiểm tra lại nhé.");
    else next();
  };
  return (
    <section className="screen form-screen">
      <TopBar onBack={back} action={<button className="skip">Thêm sau</button>} />
      <Progress value={60} />
      <div className="form-hero">
        <span className="round-icon"><CalendarBlank size={32}/></span>
        <p className="eyebrow">Mảnh ghép đầu tiên</p>
        <h1>Bạn đến với thế giới vào ngày nào?</h1>
        <p>Chỉ ngày sinh thôi. Giờ và nơi sinh có thể để sau.</p>
      </div>
      <label className={`field ${error ? "field--error" : ""}`}>
        <span>Ngày sinh</span>
        <div><input type="date" value={date} onChange={(e) => { setDate(e.target.value); setError(""); }} /></div>
        {error && <small><WarningCircle size={16}/>{error}</small>}
      </label>
      <div className="privacy-note"><ShieldCheck size={20}/><span>Ngày sinh không bao giờ xuất hiện trên nội dung bạn chia sẻ.</span></div>
      <div className="sticky-actions">
        <PrimaryButton onClick={submit}>Đọc bầu trời của mình</PrimaryButton>
      </div>
    </section>
  );
}

function Loading({ next }) {
  useEffect(() => { const id = setTimeout(next, 2200); return () => clearTimeout(id); }, [next]);
  return (
    <section className="screen screen--loading">
      <Celestial className="celestial--loading" />
      <div className="loader-orbit"><span /></div>
      <p className="eyebrow">14.08.2001</p>
      <h1>Đang đọc bầu trời<br/>lúc bạn sinh ra...</h1>
      <p>Chúng mình đang tìm vị trí Mặt Trời của bạn.</p>
      <div className="loading-steps"><span className="done">Ngày sinh</span><span className="active">Sun sign</span><span>Note đầu tiên</span></div>
    </section>
  );
}

function ProfileReveal({ next, backHome }) {
  return (
    <section className="screen reveal-screen">
      <Celestial className="celestial--reveal" />
      <p className="eyebrow">Lá Khai Sinh · lớp đầu tiên</p>
      <h1>Mặt Trời<br/><em>Sư Tử</em></h1>
      <div className="element-pill">LỬA · TỎA SÁNG · ẤM ÁP</div>
      <article className="paper paper--reveal">
        <p className="hand-note">một điều rất bạn</p>
        <h2>Bạn không cần cố nổi bật.</h2>
        <p>Bạn bước vào đâu là không khí ở đó tự đổi khác. Không phải vì bạn luôn nói lớn, mà vì cách bạn quan tâm khiến người khác cảm thấy mình được nhìn thấy.</p>
      </article>
      <div className="reveal-actions">
        <PrimaryButton onClick={next}>Tạo Lá Khai Sinh</PrimaryButton>
        <button className="text-button" onClick={backHome}>Bỏ qua, vào app</button>
      </div>
    </section>
  );
}

function BirthCard({ next, back }) {
  const [showName, setShowName] = useState(false);
  const [format, setFormat] = useState("story");
  return (
    <section className="screen card-screen">
      <TopBar onBack={back} action={<span className="step-label">Xem trước</span>} />
      <div className="format-switch">
        <button className={format === "story" ? "active" : ""} onClick={() => setFormat("story")}>Story 9:16</button>
        <button className={format === "post" ? "active" : ""} onClick={() => setFormat("post")}>Post 1:1</button>
      </div>
      <div className={`share-card ${format === "post" ? "share-card--square" : ""}`}>
        <div className="share-card__brand">Lá Lành*</div>
        {showName && <div className="share-card__name">AN · 14.08.2001</div>}
        <p className="share-card__eyebrow">LÁ KHAI SINH</p>
        <h1>Mặt Trời<br/>Sư Tử</h1>
        <div className="share-card__grid">
          <span><b>Kiểu người</b>Ấm áp nhưng không dễ đoán.</span>
          <span><b>Điểm mạnh</b>Làm người khác thấy được nhìn thấy.</span>
          <span><b>Điểm dễ mệt</b>Phải luôn là người giữ lửa.</span>
          <span><b>Lời nhắn</b>Bạn không cần sáng mọi lúc.</span>
        </div>
        <Celestial className="celestial--card" />
      </div>
      <label className="toggle-row"><span><b>Hiện tên trên card</b><small>Mặc định luôn ẩn danh.</small></span><input type="checkbox" checked={showName} onChange={(e) => setShowName(e.target.checked)}/><i/></label>
      <div className="two-actions">
        <SecondaryButton icon={<BookmarkSimple size={20}/>} onClick={() => {}}>Lưu ảnh</SecondaryButton>
        <PrimaryButton icon={<ShareNetwork size={20}/>} onClick={next}>Chia sẻ</PrimaryButton>
      </div>
    </section>
  );
}

function AppNav({ active, go }) {
  return (
    <nav className="app-nav">
      <button className={active === "home" ? "active" : ""} onClick={() => go("home")}><House size={23}/><span>Hôm nay</span></button>
      <button><Planet size={23}/><span>Khám phá</span></button>
      <button className={active === "saved" ? "active" : ""} onClick={() => go("saved")}><BookmarkSimple size={23}/><span>Đã lưu</span></button>
      <button className={active === "profile" ? "active" : ""} onClick={() => go("profileSettings")}><User size={23}/><span>Mình</span></button>
    </nav>
  );
}

function HomeScreen({ go }) {
  const [mood, setMood] = useState("Rực");
  const [saved, setSaved] = useState(false);
  const [toast, setToast] = useState("");
  const notify = (text) => { setToast(text); setTimeout(() => setToast(""), 1800); };
  return (
    <section className="screen home-screen">
      <header className="home-header"><Brand compact/><button className="profile-badge" onClick={() => go("profileSettings")}><User size={24}/><StarFour size={13} weight="fill"/></button></header>
      <div className="home-intro"><h2>Này An,</h2><span className="transit-pill"><Planet size={17} weight="fill"/> Moon tam hợp Neptune</span></div>
      <Celestial className="celestial--home" />
      <article className="paper daily-note">
        <p className="hand-note">vũ trụ để lại<br/>cho bạn một note</p>
        <h1>Đừng vội rep.</h1>
        <i />
        <p>Hôm nay cảm xúc đi trước lý trí một nhịp. Cho mình vài phút trước khi nói điều sẽ phải giải thích cả tối.</p>
      </article>
      <section className="mood-section">
        <h3>Vibe hiện tại?</h3>
        <div className="mood-row">
          {moods.map((item) => (
            <button key={item.id} className={mood === item.id ? "active" : ""} onClick={() => { setMood(item.id); notify(`Đã ghi lại vibe “${item.id}”`); }}>
              <span>{item.glyph}</span><small>{item.id}</small>
            </button>
          ))}
        </div>
      </section>
      <div className="home-actions">
        <PrimaryButton icon={<PaperPlaneTilt size={20} weight="fill"/>} onClick={() => go("share")}>Chia sẻ</PrimaryButton>
        <SecondaryButton icon={<BookmarkSimple size={20} weight={saved ? "fill" : "regular"}/>} onClick={() => { setSaved(!saved); notify(saved ? "Đã bỏ lưu" : "Đã lưu vào Lá của bạn"); }}>{saved ? "Đã lưu" : "Lưu lại"}</SecondaryButton>
      </div>
      <section className="unlock-note">
        <Moon size={38} weight="duotone"/>
        <div><b>Còn một note chưa mở</b><span>Thêm giờ sinh để bật mí Moon sign</span></div>
        <button onClick={() => go("birthTime")}>Mở khóa</button>
        <button className="quiet" onClick={() => notify("Được rồi, mình sẽ nhắc lại sau 3 ngày")}>Để sau</button>
      </section>
      <AppNav active="home" go={go}/>
      {toast && <div className="toast"><CheckCircle size={20} weight="fill"/>{toast}</div>}
    </section>
  );
}

function ShareSheet({ back }) {
  const [done, setDone] = useState(false);
  return (
    <section className="screen share-screen">
      <TopBar onBack={back} action={<span className="step-label">Chia sẻ note</span>} />
      <div className="mini-share-note">
        <p>vũ trụ để lại một note</p>
        <h1>Đừng vội rep.</h1>
        <span>Moon tam hợp Neptune</span>
        <Brand compact />
      </div>
      <h2>Gửi note này tới đâu?</h2>
      <div className="share-channels">
        {["Instagram", "Threads", "Messenger", "Zalo"].map((item, index) => <button key={item} onClick={() => setDone(true)}><span>{["IG","@","M","Z"][index]}</span>{item}</button>)}
      </div>
      <SecondaryButton icon={<ShareNetwork size={20}/>} onClick={() => setDone(true)}>Thêm lựa chọn</SecondaryButton>
      <p className="share-privacy"><EyeSlash size={17}/> Note này không hiển thị tên hoặc ngày sinh của bạn.</p>
      {done && <div className="success-overlay"><div><CheckCircle size={54} weight="fill"/><h2>Note đã sẵn sàng</h2><p>Trong prototype, đây là trạng thái mở native share sheet.</p><PrimaryButton onClick={back}>Quay lại Lá Lành</PrimaryButton></div></div>}
    </section>
  );
}

function BirthTime({ next, back }) {
  const [unknown, setUnknown] = useState(false);
  const [period, setPeriod] = useState("Sáng");
  const [time, setTime] = useState("08:30");
  return (
    <section className="screen form-screen">
      <TopBar onBack={back} action={<button className="skip" onClick={back}>Để sau</button>} />
      <div className="form-hero">
        <span className="round-icon"><Clock size={32}/></span>
        <p className="eyebrow">Mở lớp cảm xúc</p>
        <h1>Bạn sinh vào khoảng mấy giờ?</h1>
        <p>Giờ sinh giúp tìm Moon sign — cách bạn xử lý cảm xúc khi không ai nhìn.</p>
      </div>
      {!unknown ? (
        <label className="field"><span>Giờ sinh</span><div><input type="time" value={time} onChange={(e) => setTime(e.target.value)}/></div></label>
      ) : (
        <div className="period-grid">{["Sáng", "Trưa", "Chiều", "Tối"].map((p) => <button className={period === p ? "active" : ""} onClick={() => setPeriod(p)} key={p}>{p}<small>{p === "Sáng" ? "05–10h" : p === "Trưa" ? "10–14h" : p === "Chiều" ? "14–18h" : "18–24h"}</small></button>)}</div>
      )}
      <label className="check-row"><input type="checkbox" checked={unknown} onChange={(e) => setUnknown(e.target.checked)}/><i><Check size={15} weight="bold"/></i><span><b>Mình không nhớ chính xác</b><small>Chọn một khoảng giờ gần đúng.</small></span></label>
      <div className="accuracy-note"><Info size={19}/><span>{unknown ? "Kết quả sẽ là ước tính và được ghi chú rõ." : "Giờ càng chính xác, Moon sign càng đáng tin cậy."}</span></div>
      <div className="sticky-actions"><PrimaryButton onClick={next}>Tìm Moon sign</PrimaryButton></div>
    </section>
  );
}

function MoonLoading({ next }) {
  useEffect(() => { const id = setTimeout(next, 1900); return () => clearTimeout(id); }, [next]);
  return <section className="screen screen--loading moon-loading"><Moon size={100} weight="duotone"/><div className="loader-orbit"><span/></div><p className="eyebrow">Lớp thứ hai</p><h1>Đang tìm Mặt Trăng<br/>của riêng bạn...</h1><p>Đối chiếu bầu trời lúc 08:30 · 14.08.2001</p></section>;
}

function MoonReveal({ home }) {
  return (
    <section className="screen reveal-screen moon-reveal">
      <Celestial className="celestial--reveal" />
      <p className="eyebrow">Moon sign đã mở</p>
      <h1>Mặt Trăng<br/><em>Song Tử</em></h1>
      <div className="element-pill">KHÍ · LINH HOẠT · TÒ MÒ</div>
      <article className="paper paper--reveal">
        <p className="hand-note">khi không ai nhìn</p>
        <h2>Bạn gọi tên cảm xúc bằng câu hỏi.</h2>
        <p>Khi một điều chạm sâu, bạn thường muốn hiểu nó trước khi cho phép mình cảm thấy. Nói ra không làm cảm xúc nhỏ đi — nó giúp bạn tìm được chỗ đặt nó xuống.</p>
      </article>
      <div className="level-up"><Sparkle size={20} weight="fill"/><span><b>Hồ sơ lên Level 2</b>Daily Astro từ ngày mai sẽ đọc cả Sun + Moon.</span></div>
      <PrimaryButton onClick={home}>Xem note hôm nay</PrimaryButton>
    </section>
  );
}

function Saved({ go }) {
  return (
    <section className="screen library-screen">
      <TopBar action={<button className="icon-button"><MagnifyingGlass size={22}/></button>} />
      <div className="library-title"><p className="eyebrow">Bộ sưu tập riêng</p><h1>Những note bạn muốn giữ lại.</h1></div>
      <div className="filter-row"><button className="active">Tất cả</button><button>Daily note</button><button>Lá Khai Sinh</button></div>
      <div className="saved-grid">
        <article><span>21.06</span><h3>Đừng vội rep.</h3><p>Moon tam hợp Neptune</p></article>
        <article className="lime"><span>Lá Khai Sinh</span><h3>Mặt Trời Sư Tử</h3><p>Ấm áp nhưng không dễ đoán.</p></article>
        <article><span>18.06</span><h3>Đừng tự làm nhỏ điều bạn cần.</h3><p>Venus vuông Saturn</p></article>
      </div>
      <AppNav active="saved" go={go}/>
    </section>
  );
}

function ProfileSettings({ go }) {
  return (
    <section className="screen profile-screen">
      <TopBar />
      <div className="profile-card"><div className="profile-avatar">A</div><div><p className="eyebrow">HỒ SƠ LEVEL 2</p><h1>An</h1><span>Sun Sư Tử · Moon Song Tử</span></div></div>
      <div className="profile-progress"><div><b>2/5 lớp đã mở</b><span>Thêm nơi sinh để mở bản đồ kết nối.</span></div><Progress value={40}/></div>
      <div className="settings-list">
        <button><CalendarBlank size={22}/><span><b>Dữ liệu sinh</b><small>14.08.2001 · 08:30 · Chưa có nơi sinh</small></span><ArrowRight/></button>
        <button><ShieldCheck size={22}/><span><b>Quyền riêng tư & dữ liệu</b><small>Xem, tải xuống hoặc xóa dữ liệu</small></span><ArrowRight/></button>
        <button><StarFour size={22}/><span><b>Tùy chọn nội dung</b><small>Thông báo, giọng điệu và lịch nhắc</small></span><ArrowRight/></button>
      </div>
      <button className="danger-link">Đăng xuất</button>
      <AppNav active="profile" go={go}/>
    </section>
  );
}

export function App() {
  const [screen, setScreen] = useState(() => {
    const query = new URLSearchParams(window.location.search);
    const requested = query.get("screen");
    return screens.includes(requested) ? requested : "welcome";
  });
  const go = (name) => {
    setScreen(name);
    window.history.replaceState({}, "", `?screen=${name}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const backMap = {
    consent: "welcome", auth: "consent", otp: "auth", birth: "otp", profile: "birth",
    card: "profile", share: "home", birthTime: "home",
  };
  return (
    <div className="prototype-shell">
      {screen === "welcome" && <Welcome next={() => go("consent")} />}
      {screen === "consent" && <Consent next={() => go("auth")} back={() => go("welcome")} />}
      {screen === "auth" && <Auth next={() => go("otp")} back={() => go("consent")} />}
      {screen === "otp" && <OTP next={() => go("birth")} back={() => go("auth")} />}
      {screen === "birth" && <BirthDate next={() => go("loading")} back={() => go("otp")} />}
      {screen === "loading" && <Loading next={() => go("profile")} />}
      {screen === "profile" && <ProfileReveal next={() => go("card")} backHome={() => go("home")} />}
      {screen === "card" && <BirthCard next={() => go("home")} back={() => go("profile")} />}
      {screen === "home" && <HomeScreen go={go} />}
      {screen === "share" && <ShareSheet back={() => go("home")} />}
      {screen === "birthTime" && <BirthTime next={() => go("moonLoading")} back={() => go("home")} />}
      {screen === "moonLoading" && <MoonLoading next={() => go("moonReveal")} />}
      {screen === "moonReveal" && <MoonReveal home={() => go("home")} />}
      {screen === "saved" && <Saved go={go} />}
      {screen === "profileSettings" && <ProfileSettings go={go} />}
    </div>
  );
}
