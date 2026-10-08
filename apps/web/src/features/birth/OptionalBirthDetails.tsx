import { CaretDown, Clock } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { searchBirthPlaces } from "../../shared/api/client";
import { BirthTimeInput } from "../../shared/ui/BirthTimeInput";
import { emptyBirthDetails, hasBirthDetails, type OptionalBirthInput } from "./optionalBirthInput";

export function OptionalBirthDetails({ value, onChange, disabled, error }: {
  value: OptionalBirthInput;
  onChange: (value: OptionalBirthInput) => void;
  disabled: boolean;
  error: string | null;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [showAll, setShowAll] = useState(false);
  const expanded = open || Boolean(error);
  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(value.placeText.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [value.placeText]);
  const places = useQuery({
    queryKey: ["birth-places", showAll ? "all-current" : query],
    queryFn: ({ signal }) => searchBirthPlaces(showAll ? "" : query, signal),
    enabled: expanded && !disabled && !value.place && (showAll || query.length >= 2),
    retry: false,
  });
  function update(patch: Partial<OptionalBirthInput>) {
    onChange({ ...value, ...patch, consented: patch.consented ?? false });
  }
  function skip() {
    onChange({ ...emptyBirthDetails });
    setShowAll(false);
    setOpen(false);
  }
  return <section className="birth-optional">
    <button aria-expanded={expanded} aria-controls="birth-optional-fields" className="birth-optional__trigger" disabled={disabled} onClick={() => setOpen(!expanded)} type="button">
      <Clock aria-hidden="true" size={22} />
      <span><strong>Thêm giờ & nơi sinh</strong><small>Không bắt buộc · để hiểu mình rõ hơn</small></span>
      <CaretDown aria-hidden="true" size={18} />
    </button>
    {expanded ? <fieldset aria-describedby={error ? "birth-error" : undefined} className="birth-optional__fields" disabled={disabled} id="birth-optional-fields">
      <legend className="sr-only">Thông tin sinh không bắt buộc</legend>
      <p>Biết giờ và nơi sinh? Thêm để mở bản đọc tổng quan về cảm xúc, cách kết nối và những điều bạn thường gặp.</p>
      <BirthTimeInput mode={value.mode} onModeChange={(mode) => update({ mode })} time={value.time} onTimeChange={(time) => update({ time })} window={value.window} onWindowChange={(window) => update({ window })} />
      <label><span>Nơi sinh · có thể thêm sau</span><input autoComplete="off" maxLength={80} placeholder="Tìm thành phố / tỉnh" value={value.placeText} onChange={(event) => { setShowAll(false); update({ placeText: event.target.value, place: null }); }} /></label>
      {!value.place ? <button className="detail-link" onClick={() => setShowAll(!showAll)} type="button">{showAll ? "Thu gọn danh mục" : "Xem đủ 34 tỉnh/thành"}</button> : <p className="birth-optional__precision">Đã chọn: {value.place.display_name}</p>}
      {places.isFetching ? <small role="status">Đang tìm nơi sinh…</small> : null}
      {!value.place && places.isError ? <div role="alert"><small>Chưa tải được danh sách. Bạn có thể thử lại hoặc thêm nơi sinh sau.</small><button className="detail-link" onClick={() => void places.refetch()} type="button">Thử tải lại nơi sinh</button></div> : null}
      {!value.place && (showAll || query === value.placeText.trim()) && places.data?.length ? <div className="place-results" aria-label="Danh sách nơi sinh">{places.data.map((place) => <button key={place.place_id} type="button" onClick={() => { setShowAll(false); update({ place, placeText: place.display_name }); }}><strong>{place.display_name}</strong><span>{place.confidence === "former-province-centroid" ? "Tên địa phương trước sắp xếp" : "Danh mục hiện hành"}</span></button>)}</div> : null}
      {!value.place && !places.isFetching && !places.isError && places.data?.length === 0 && (showAll || query.length >= 2) ? <small>Chưa thấy nơi này. Thử tên tỉnh hiện hành hoặc tên tỉnh cũ nhé.</small> : null}
      <small className="birth-optional__precision">{value.mode === "unknown" ? "Chưa biết giờ vẫn đọc được Note. Lá không đoán giờ sinh thay bạn." : value.mode === "approx_window" ? "Giờ gần đúng: không dùng để khẳng định cung Mọc hay nhà chính xác." : !/^([01]\d|2[0-3]):[0-5]\d$/.test(value.time) ? "Chọn cả giờ và phút. Không nhớ rõ thì chọn khoảng giờ hoặc để sau nhé." : !value.place ? "Chỉ có giờ chưa đủ để tính cung Mọc và nhà. Bạn có thể bổ sung nơi sinh sau." : "Đã đủ thông tin để tính bản đọc tổng quan; nội dung vẫn là góc nhìn tham khảo."}</small>
      {hasBirthDetails(value) ? <label className="birth-optional__consent"><input type="checkbox" checked={value.consented} onChange={(event) => update({ consented: event.target.checked })} /><span>Tôi đồng ý dùng giờ/nơi sinh để tính lá số và cá nhân hóa bản đọc. Không đưa lên nội dung chia sẻ. Có thể xóa trong Mình. <Link to="/privacy" target="_blank" rel="noopener noreferrer">Quyền riêng tư</Link></span></label> : null}
      <button className="text-button" onClick={skip} type="button">Bỏ qua giờ & nơi sinh</button>
    </fieldset> : null}
    {!expanded && hasBirthDetails(value) ? <small className="birth-optional__summary">Đã chọn thông tin bổ sung{value.consented ? " · đã đồng ý sử dụng" : " · cần xác nhận sử dụng"}</small> : null}
  </section>;
}
