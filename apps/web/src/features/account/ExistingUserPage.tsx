import { ArrowLeft, GoogleLogo } from "@phosphor-icons/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import {
  acceptBasicBirthConsent, ApiProblem, cancelAccountLogin, createGuest, getAccountStatus,
  getSession, isGuestSessionUnavailable, requestGoogleLogin, restoreAccount, verifyGoogleLogin,
  type AccountLoginResult,
} from "../../shared/api/client";
import "./account.css";

const SAFE_RETURNS = new Set(["/home", "/profile", "/saved", "/radar", "/tarot", "/reveal"]);

function loginError(error: unknown): string {
  if (!(error instanceof ApiProblem)) return "Chưa kết nối được. Hồ sơ trên máy này vẫn được giữ.";
  if (error.code === "LOGIN_LIMITED") return "Bạn thử hơi nhanh rồi. Chờ một chút trước khi đăng nhập lại nhé.";
  if (["LOGIN_CHALLENGE_EXPIRED", "LOGIN_CHALLENGE_USED", "LOGIN_CHALLENGE_REJECTED"].includes(error.code)) return "Lần đăng nhập này đã hết hạn hoặc phiên trên máy đã đổi. Đăng nhập lại nhé.";
  if (error.code === "LOGIN_UNAVAILABLE") return "Google chưa được bật trên bản này. Bạn vẫn dùng được hồ sơ khách.";
  return "Chưa xác nhận được tài khoản Google. Hồ sơ hiện tại chưa bị thay đổi.";
}

export function ExistingUserPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const requestedReturn = new URLSearchParams(location.search).get("returnTo");
  const returnTo = requestedReturn && SAFE_RETURNS.has(requestedReturn) ? requestedReturn : "/home";
  const account = useQuery({ queryKey: ["optional-account"], queryFn: ({ signal }) => getAccountStatus(signal), retry: false });
  const [consent, setConsent] = useState(false);
  const [restore, setRestore] = useState<AccountLoginResult | null>(null);
  const [outcome, setOutcome] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [callback] = useState(() => {
    if (location.pathname !== "/auth/callback") return null;
    const params = new URLSearchParams(location.search);
    return { code: params.get("code"), state: params.get("state"), denied: params.has("error") };
  });
  const exchange = useRef<Promise<AccountLoginResult> | null>(null);
  const restoreNonce = callback?.state ?? null;
  const guestKey = useRef(crypto.randomUUID());
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);

  async function adopt(result: AccountLoginResult) {
    if (!alive.current) return;
    if (result.status === "signed_in") {
      if (!result.session) throw new Error("missing verified session");
      await queryClient.cancelQueries();
      queryClient.clear();
      if (alive.current) void navigate(result.session.onboarding_status === "birth_pending" ? "/birth" : returnTo, { replace: true });
    } else if (result.status === "restore_required") setRestore(result);
    else setOutcome(result.status);
  }

  useEffect(() => {
    if (!callback) return;
    // Strip OAuth code/state/error before any user action or outbound link.
    // Proof stays only in component memory; refreshing requires a new login.
    window.history.replaceState(window.history.state, "", location.pathname);
    if (callback.denied) { setError("Bạn chưa hoàn tất đăng nhập Google. Hồ sơ hiện tại trên máy này vẫn được giữ."); return; }
    if (!callback.code || !callback.state || !/^[A-Za-z0-9_-]{43}$/.test(callback.state)) {
      setError("Thiếu xác nhận Google. Đăng nhập lại để tiếp tục nhé."); return;
    }
    let mounted = true;
    setPending(true);
    // StrictMode replays effects: reuse the in-memory promise, not the code.
    exchange.current ??= verifyGoogleLogin(callback.code, callback.state);
    void exchange.current.then(async (result) => { if (mounted) await adopt(result); })
      .catch((failure: unknown) => { if (mounted) setError(loginError(failure)); })
      .finally(() => { if (mounted) setPending(false); });
    return () => { mounted = false; };
    // Callback is immutable; adopt uses this screen's allowlisted return.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callback]);

  async function signIn() {
    if (pending || !consent || !account.data?.google_login_enabled) return;
    setPending(true); setError(null);
    try {
      try { await getSession(); await acceptBasicBirthConsent(); }
      catch (failure) { if (!isGuestSessionUnavailable(failure)) throw failure; await createGuest(guestKey.current); }
      const result = await requestGoogleLogin();
      if (!alive.current) return;
      const url = new URL(result.authorize_url);
      if (url.protocol !== "https:" || !/^[a-z0-9]{20}\.supabase\.co$/.test(url.hostname)
        || url.port || url.username || url.password || url.hash || url.pathname !== "/auth/v1/authorize") throw new Error("invalid authorize URL");
      window.location.assign(url.href);
    } catch (failure) { if (alive.current) { setError(loginError(failure)); setPending(false); } }
  }

  async function cancel() {
    if (pending) return;
    setPending(true); setError(null);
    try {
      if (restoreNonce) await cancelAccountLogin(restoreNonce);
      void navigate(requestedReturn && SAFE_RETURNS.has(requestedReturn) ? returnTo : "/welcome", { replace: true });
    } catch (failure) {
      if (failure instanceof ApiProblem && ["LOGIN_CHALLENGE_REJECTED", "LOGIN_CHALLENGE_EXPIRED"].includes(failure.code)) void navigate("/welcome", { replace: true });
      else setError(loginError(failure));
    } finally { if (alive.current) setPending(false); }
  }

  return <main className="flow-page account-page" aria-busy={pending || undefined}>
    <header className="flow-header uv-topbar"><button aria-label="Quay lại" className="icon-button uv-topbar__icon" disabled={pending} onClick={() => void cancel()} type="button"><ArrowLeft /></button><span /><span aria-hidden="true" className="uv-topbar__spacer" /></header>
    <section className="account-card" aria-labelledby="account-title">
      <img alt="" className="account-card__art" src="/assets/ultraviolet/pair.webp" />
      <p className="accent-kicker eyebrow">Đăng nhập tuỳ chọn</p>
      <h1 id="account-title">Đổi máy, vẫn là hồ sơ của bạn.</h1>
      <p>Đăng nhập bằng Google để mở lại hồ sơ. Không đăng nhập vẫn dùng được trên máy này.</p>
      {pending ? <p role="status">Đang xác nhận với Google…</p> : null}
      {restore ? <>
        <h2>Mở lại hồ sơ đã giữ?</h2>
        <p>Tài khoản {restore.masked_email} đã có hồ sơ. Mở hồ sơ đó sẽ thay hồ sơ đang hiển thị trên máy này, không gộp hai người hay chép lịch sử qua lại.</p>
        <p>Hồ sơ khách chưa chọn vẫn theo thời hạn cũ. Quyền đồng ý AI của hai hồ sơ không được gộp.</p>
        <button className="electric-button" disabled={pending} onClick={() => {
          if (pending || !restoreNonce) return;
          setPending(true); setError(null);
          void restoreAccount(restoreNonce).then(adopt).catch((failure: unknown) => setError(loginError(failure))).finally(() => { if (alive.current) setPending(false); });
        }} type="button">Mở hồ sơ của tài khoản này</button>
      </> : callback ? <>{outcome ? <p role="status">Tài khoản chưa liên kết được với hồ sơ trên máy này. Hồ sơ hiện tại vẫn được giữ.</p> : null}{!pending ? <Link className="electric-button" to="/existing-user">Đăng nhập lại bằng Google</Link> : null}</> : account.isPending ? <p role="status">Đang kiểm tra đăng nhập…</p> : account.isError ? <><p role="alert">Chưa kiểm tra được. Hồ sơ khách vẫn được giữ.</p><button className="text-button" onClick={() => void account.refetch()} type="button">Thử lại</button></> : account.data.signed_in ? <><p role="status">Đã đăng nhập · {account.data.masked_email}</p><Link className="electric-button" to="/profile">Về hồ sơ của mình</Link></> : <>
        <label className="account-consent"><input checked={consent} disabled={pending} onChange={(event) => setConsent(event.target.checked)} type="checkbox" /><span>Đồng ý dùng thông tin sinh bạn nhập để tạo hồ sơ và giữ hồ sơ tới 365 ngày không sử dụng. Note ngày tự động hiện tối đa 24 giờ (có thể được dọn sớm hơn), lịch sử khác tối đa 30 ngày; note chủ động lưu giữ cùng hồ sơ. Có thể xoá trong Mình.</span></label>
        <p className="account-footnote">Google và Supabase xác thực tài khoản. Lá chỉ giữ mã tài khoản và email đã che bớt; không đọc Gmail hay danh bạ. Đăng nhập không đồng nghĩa đồng ý gửi nội dung cho AI. <Link to="/privacy">Quyền riêng tư</Link>.</p>
        {!account.data.google_login_enabled ? <p role="status">Đăng nhập Google chưa bật trên bản này. Hồ sơ khách vẫn dùng bình thường.</p> : null}
        <button className="electric-button" disabled={pending || !consent || !account.data.google_login_enabled} onClick={() => void signIn()} type="button"><GoogleLogo aria-hidden="true" /> Tiếp tục với Google</button>
      </>}
      {error ? <p className="inline-error" role="alert">{error}</p> : null}
      <button className="text-button" disabled={pending} onClick={() => void cancel()} type="button">{restore ? "Giữ hồ sơ trên máy này" : "Tiếp tục không đăng nhập"}</button>
    </section>
  </main>;
}
