import type { ApproxWindow, BirthTimeMode } from "../api/client";
import { BirthTimePicker } from "./BirthTimePicker";
import { birthTimeWindows as windows } from "./birthTimeOptions";

const allModes: BirthTimeMode[] = ["exact", "approx_window", "unknown"];
/** One presentation; callers expose only precision modes their API supports. */
export function BirthTimeInput({ mode, onModeChange, time, onTimeChange,
  window = "morning", onWindowChange, modes = allModes,
  unknownLabel = "Chưa biết", unknownHelp = "Không đoán giờ sinh. Bạn có thể thêm sau.",
}: {
  mode: BirthTimeMode;
  onModeChange: (mode: BirthTimeMode) => void;
  time: string;
  onTimeChange: (time: string) => void;
  window?: ApproxWindow;
  onWindowChange?: (window: ApproxWindow) => void;
  modes?: BirthTimeMode[];
  unknownLabel?: string;
  unknownHelp?: string;
}) {
  return <div className="birth-time-input">
    <div aria-label="Bạn nhớ giờ sinh thế nào?" className="segmented-control birth-time-input__modes" role="group">
      {modes.filter((item) => item !== "approx_window" || onWindowChange).map((item) =>
        <button aria-pressed={mode === item} className={mode === item ? "is-active" : ""} key={item} onClick={() => onModeChange(item)} type="button">
          {item === "exact" ? "Biết giờ" : item === "approx_window" ? "Nhớ khoảng" : unknownLabel}
        </button>)}
    </div>
    {mode === "exact" ? <BirthTimePicker value={time} onChange={onTimeChange} /> : null}
    {mode === "approx_window" && onWindowChange ? <div aria-label="Khoảng giờ sinh" className="window-grid" role="group">
      {windows.map((item) => <button aria-pressed={window === item.value} className={window === item.value ? "is-active" : ""} key={item.value} onClick={() => onWindowChange(item.value)} type="button"><strong>{item.label}</strong><span>{item.hint}</span></button>)}
    </div> : null}
    {mode === "unknown" ? <p className="birth-time-input__help">{unknownHelp}</p> : null}
  </div>;
}
