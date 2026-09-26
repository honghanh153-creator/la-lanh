import { ArrowLeft, EyeSlash, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  deleteLaChungResult,
  getLaChungResult,
  hideLaChungResult,
} from "../../shared/api/client";
import "./la-chung.css";

export function ResultPage() {
  const { requestId = "" } = useParams();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const query = useQuery({
    queryKey: ["la-chung-result", requestId],
    queryFn: ({ signal }) => getLaChungResult(requestId, signal),
    retry: false,
  });
  const finish = async () => {
    await cache.invalidateQueries({ queryKey: ["la-chung-invites"] });
    void navigate("/la-chung/history", { replace: true });
  };
  const hide = useMutation({
    mutationFn: () => hideLaChungResult(requestId),
    onSuccess: finish,
  });
  const remove = useMutation({
    mutationFn: () => deleteLaChungResult(requestId),
    onSuccess: finish,
  });

  return <main className="flow-page la-chung-page">
    <header className="cosmic-header">
      <Link className="icon-button" to="/la-chung/history"><ArrowLeft /></Link>
      <span className="eyebrow">Một Lá Chứng</span><span />
    </header>
    {query.data ? <>
      <section className="result-hero"><Sparkle weight="fill" /><p>{query.data.display_alias ? `Từ ${query.data.display_alias}` : "Một người đã chọn ẩn danh"}</p><h1>Họ nhìn thấy<br />những điều này ở bạn.</h1></section>
      <section className="result-stack">{query.data.statements.map((statement, index) => <article key={statement}><span>0{index + 1}</span><p>{statement}</p></article>)}</section>
      <aside className="result-privacy"><EyeSlash /><p>Kết quả này đứng riêng, không được dùng để chấm điểm hay đưa vào matching.</p></aside>
      <div className="flow-actions">
        <button className="outline-button" disabled={hide.isPending || remove.isPending} onClick={() => hide.mutate()} type="button">Ẩn kết quả</button>
        <button className="text-button" disabled={hide.isPending || remove.isPending} onClick={() => remove.mutate()} type="button">Xóa vĩnh viễn</button>
        {hide.isError || remove.isError ? <p role="alert">Chưa thực hiện được. Thử lại khi kết nối ổn hơn.</p> : null}
      </div>
    </> : <section className="cosmic-state"><h1>Lá Chứng này không còn mở.</h1><p>Phản hồi có thể đã được rút, ẩn hoặc xóa.</p></section>}
  </main>;
}
