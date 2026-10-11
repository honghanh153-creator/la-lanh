import { VIBE_LABEL, type AppVibe } from "./vibe";
import { useVibe } from "./useVibe";
import "./vibe-picker.css";

const VIBE_SAMPLE: Record<AppVibe, string> = {
  direct: "“Hôm nay dễ mở nhiều việc cùng lúc. Chọn một việc cũ để làm xong.”",
  roast: "“Não đang mở 12 tab mà tab nào cũng ‘đang tải’. Đóng bớt một cái đi bạn ơi.”",
};

/** "Giọng của Lá": a two-option segmented control. Only wording changes. */
export function VibeSegmented() {
  const { vibe, setVibe } = useVibe();
  return (
    <div className="vibe-segmented">
      <p className="vibe-segmented__label" id="vibe-segmented-label">Giọng của Lá</p>
      <div aria-labelledby="vibe-segmented-label" className="vibe-segmented__track" role="radiogroup">
        {(Object.keys(VIBE_LABEL) as AppVibe[]).map((key) => (
          <button
            aria-checked={vibe === key}
            key={key}
            onClick={() => setVibe(key)}
            role="radio"
            type="button"
          >
            {VIBE_LABEL[key].title}
          </button>
        ))}
      </div>
      <p className="vibe-segmented__sample" aria-live="polite">{VIBE_SAMPLE[vibe]}</p>
    </div>
  );
}
