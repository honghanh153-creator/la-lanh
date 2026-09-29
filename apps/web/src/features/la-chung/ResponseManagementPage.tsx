import { ArrowLeft, Check, Trash } from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ApiProblem, withdrawLaChungResponse } from "../../shared/api/client";
import "./la-chung.css";

export function ResponseManagementPage() {
  const withdraw = useMutation({ mutationFn: withdrawLaChungResponse });
  const missingReceipt = withdraw.error instanceof ApiProblem && withdraw.error.status === 404;

  return (
    <main className="flow-page la-chung-page">
      <header className="cosmic-header">
        <Link aria-label="Quay lại" className="icon-button" to="/la-chung"><ArrowLeft /></Link>
        <span className="eyebrow">Quản lý phản hồi cũ</span><span />
      </header>
      <section className="insight-hero">
        <h1>Rút phản hồi trên thiết bị này.</h1>
        <p>Nếu trình duyệt này còn receipt hợp lệ, Lá Lành sẽ rút phản hồi đã gửi và xóa quyền mở lại của receipt đó.</p>
      </section>
      <section className="cosmic-state">
        {withdraw.isSuccess ? <><Check size={36} /><h2>Phản hồi đã được rút.</h2><p>Nội dung không còn hiển thị cho người nhận.</p><Link className="electric-button" to="/home">Về Lá Lành</Link></> : <><Trash size={36} /><h2>Chỉ thực hiện khi bạn muốn rút.</h2><p>Trang này không đọc link mời hoặc nội dung phản hồi trước khi bạn bấm.</p><button className="outline-button" disabled={withdraw.isPending} onClick={() => withdraw.mutate()} type="button">{withdraw.isPending ? "Đang rút…" : "Rút phản hồi đã gửi"}</button></>}
        {withdraw.isError ? <p role="alert">{missingReceipt ? "Không tìm thấy receipt còn hiệu lực trên thiết bị này, hoặc phản hồi đã được rút trước đó." : "Chưa kết nối được để rút phản hồi. Không có thay đổi nào được xác nhận; hãy thử lại khi mạng ổn hơn."}</p> : null}
      </section>
    </main>
  );
}
