import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { getMonthOverview, getMonthStatus } from "../../shared/api/client";
import { monthCopy } from "./monthCopy";
import { monthReminderOn, setMonthReminder } from "./monthReminder";
import { MONTH_STATUS_KEY } from "./monthQueries";

/** "Tháng N của bạn" in Khám phá (US-25, S21): one line and one small thing per area, no dates. */
export function MonthOverviewCard() {
  const status = useQuery({ queryKey: MONTH_STATUS_KEY, queryFn: ({ signal }) => getMonthStatus(signal), retry: false });
  const available = status.data?.available === true;
  const overview = useQuery({
    queryKey: ["month-overview"],
    queryFn: ({ signal }) => getMonthOverview(signal),
    enabled: available,
    retry: false,
  });
  const [reminder, setReminder] = useState(monthReminderOn);
  if (!available || !overview.data) return null;
  const monthNumber = Number(overview.data.month.split("-")[1]);

  return (
    <section className="month-overview" aria-labelledby="month-overview-title">
      <h2 id="month-overview-title">Tháng {monthNumber} của bạn</h2>
      <ul>
        {overview.data.items.map((item) => (
          <li key={item.area}>
            <p><strong>{item.label}:</strong> {item.line}</p>
            <p className="month-overview__try"><strong>{monthCopy("month.ui.try_label")}:</strong> {item.try_text}</p>
          </li>
        ))}
      </ul>
      <label className="month-reminder">
        <input
          checked={reminder}
          onChange={(event) => {
            setMonthReminder(event.target.checked);
            setReminder(event.target.checked);
          }}
          type="checkbox"
        />
        <span>{monthCopy("month.ui.reminder_toggle")}</span>
      </label>
    </section>
  );
}
