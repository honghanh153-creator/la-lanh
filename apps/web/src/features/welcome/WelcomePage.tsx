import { ArrowRight } from "@phosphor-icons/react";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { createGuest } from "../../shared/api/client";
import { clearPersonalDataOnDevice } from "../../shared/storage/clearPersonalData";
import { SignalStationFrame } from "../../shared/ui/SignalStationFrame";

function idempotencyKey(): string {
  const existing = sessionStorage.getItem("la-lanh-guest-create-key");
  if (existing) return existing;
  const value = crypto.randomUUID();
  sessionStorage.setItem("la-lanh-guest-create-key", value);
  return value;
}

export function WelcomePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const routeState = location.state as { expired?: boolean; offline?: boolean } | null;
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const begin = async () => {
    if (pending) return;
    setPending(true);
    setError(null);
    const key = idempotencyKey();
    try {
      await clearPersonalDataOnDevice();
      sessionStorage.setItem("la-lanh-guest-create-key", key);
      queryClient.clear();
      await createGuest(key);
      sessionStorage.removeItem("la-lanh-guest-create-key");
      void navigate("/birth", { replace: true });
    } catch {
      setError("Chưa bật được tín hiệu. Kiểm tra kết nối rồi thử lại nhé.");
    } finally {
      setPending(false);
    }
  };

  const actions = (
    <>
      <button className="signal-station__button" disabled={pending} onClick={() => void begin()} type="button">
        <span>{pending ? "Đang bật tín hiệu…" : "Đồng ý & bật tín hiệu"}</span>
        <ArrowRight aria-hidden="true" size={21} weight="bold" />
      </button>
      <Link className="signal-station__secondary" to="/demo">Xem bản mẫu</Link>
      <p className="signal-station__privacy">
        Dữ liệu dùng để tính Lá đầu tiên · <Link to="/privacy">Xem chi tiết</Link>
      </p>
    </>
  );

  return (
    <SignalStationFrame act={0} actions={actions} loading={pending} titleId="welcome-title">
      <h1 id="welcome-title">Có một tín hiệu đã đi cùng bạn từ ngày bạn xuất hiện.</h1>
      <p className="signal-station__lead">Chỉ cần ngày sinh. Chưa cần tài khoản.</p>
      <p className="signal-station__privacy">
        Phiên khách tự hết hạn sau 30 ngày không hoạt động. Bạn có thể từ chối, xem bản mẫu hoặc xóa dữ liệu bất cứ lúc nào.
      </p>
      {routeState?.expired ? (
        <p className="signal-station__notice" role="status">Phiên trước đã hết hạn. Dữ liệu cũ không còn được hiển thị; bạn có thể bắt đầu một Lá mới.</p>
      ) : null}
      {routeState?.offline ? (
        <p className="signal-station__notice" role="status">Bạn đang offline. Bản mẫu vẫn xem được mà không cần tạo phiên khách.</p>
      ) : null}
      {error ? <p className="signal-station__error" role="alert">{error}</p> : null}
    </SignalStationFrame>
  );
}
