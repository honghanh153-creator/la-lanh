type BirthTimePickerProps = {
  value: string;
  onChange: (value: string) => void;
};

/** Preserve the API's HH:mm contract without asking people to type punctuation. */
export function BirthTimePicker({ value, onChange }: BirthTimePickerProps) {
  const [hour = "", minute = ""] = value.split(":");
  return <div className="birth-time-picker" role="group" aria-label="Giờ sinh">
    <label><span>Giờ (0–23)</span><select value={hour} onChange={(event) => onChange(`${event.target.value}:${minute}`)}>
      <option value="">Chọn giờ</option>
      {Array.from({ length: 24 }, (_, index) => String(index).padStart(2, "0")).map((option) => <option key={option} value={option}>{option}</option>)}
    </select></label>
    <label><span>Phút (0–59)</span><select value={minute} onChange={(event) => onChange(`${hour}:${event.target.value}`)}>
      <option value="">Chọn phút</option>
      {Array.from({ length: 60 }, (_, index) => String(index).padStart(2, "0")).map((option) => <option key={option} value={option}>{option}</option>)}
    </select></label>
  </div>;
}
