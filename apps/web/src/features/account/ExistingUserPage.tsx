import { ArrowLeft } from "@phosphor-icons/react";
import { Link, useNavigate } from "react-router-dom";

import { BrandMark } from "../../shared/ui/BrandMark";

export function ExistingUserPage() {
  const navigate = useNavigate();
  return <main className="flow-page account-page"><header className="flow-header"><button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><BrandMark /><span /></header><section className="paper-panel"><p className="handwritten-kicker">dành cho người đã có Lá</p><h1>Đăng nhập sẽ mở ở chặng kết nối.</h1><p>MVP này chưa tạo tài khoản và không chặn bạn ở đây. Bạn vẫn có thể dùng trọn Lá Khai Sinh với chế độ khách.</p></section><Link className="electric-button" to="/consent">Tiếp tục không cần tài khoản</Link></main>;
}
