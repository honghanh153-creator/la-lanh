import { Link } from "react-router-dom";

const steps = [
  { label: "Bắt đầu", href: "/radar" },
  { label: "Thông tin", href: "/radar/start" },
  { label: "Bản đọc", href: null },
] as const;

export function RadarFlowSteps({ current }: { current: 1 | 2 | 3 }) {
  return <nav aria-label="Tiến độ Radar" className="radar-flow-steps">
    <ol>{steps.map((step, index) => {
      const number = index + 1;
      const content = <><span aria-hidden="true">{String(number).padStart(2, "0")}</span><strong>{step.label}</strong></>;
      return <li className={number === current ? "is-current" : number < current ? "is-complete" : ""} key={step.label}>
        {number === current || !step.href || number > current
          ? <span aria-current={number === current ? "step" : undefined}>{content}</span>
          : <Link to={step.href}>{content}</Link>}
      </li>;
    })}</ol>
  </nav>;
}
