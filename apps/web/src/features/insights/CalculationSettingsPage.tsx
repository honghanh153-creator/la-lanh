import { ArrowLeft, CheckCircle, SlidersHorizontal } from "@phosphor-icons/react";
import { Link, useSearchParams } from "react-router-dom";

import {
  AYANAMSA_OPTIONS,
  JYOTISH_HOUSE_OPTIONS,
  WESTERN_HOUSE_OPTIONS,
  defaultHouseSystem,
  parseAyanamsa,
  parseHouseSystem,
  parseTradition,
} from "./insightConfig";
import "./insights.css";

export function CalculationSettingsPage() {
  const [params, setParams] = useSearchParams();
  const tradition = parseTradition(params.get("tradition"));
  const house = parseHouseSystem(params.get("house")) ?? defaultHouseSystem(tradition);
  const ayanamsa = parseAyanamsa(params.get("ayanamsa")) ?? "lahiri";
  const houseOptions = tradition === "jyotish" ? JYOTISH_HOUSE_OPTIONS : WESTERN_HOUSE_OPTIONS;
  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    next.set(key, value);
    setParams(next);
  };
  return <main className="flow-page settings-page insight-settings">
    <header className="cosmic-header"><Link aria-label="Quay lại Bản đồ của mình" className="icon-button" to={`/insights?tradition=${tradition}`}><ArrowLeft /></Link><span className="eyebrow">Cách tính</span><SlidersHorizontal /></header>
    <section className="insight-hero"><h1>Biết chart được tính thế nào.</h1><p>Hai hệ đọc không phải hai nhãn cho cùng dữ liệu. Đổi hệ sẽ tính lại toàn bộ vị trí.</p></section>
    <fieldset className="calculation-group">
      <legend>Hệ nhà</legend>
      {houseOptions.map(({ value, label }) => <button aria-pressed={house === value} className={house === value ? "is-active" : ""} key={value} onClick={() => set("house", value)} type="button"><span>{label}</span>{house === value ? <CheckCircle weight="fill" /> : null}</button>)}
    </fieldset>
    {tradition === "jyotish" ? <fieldset className="calculation-group"><legend>Ayanamsa</legend>{AYANAMSA_OPTIONS.map(({ value, label }) => <button aria-pressed={ayanamsa === value} className={ayanamsa === value ? "is-active" : ""} key={value} onClick={() => set("ayanamsa", value)} type="button"><span>{label}</span>{ayanamsa === value ? <CheckCircle weight="fill" /> : null}</button>)}</fieldset> : null}
    <Link className="electric-button" to={`/insights?${params.toString()}`}>Áp dụng cách tính</Link>
    <button className="text-button" onClick={() => setParams({ tradition })} type="button">Đặt lại khuyên dùng</button>
  </main>;
}
