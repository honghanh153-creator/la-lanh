/**
 * The weekly Home reminder for the month card (US-25, S21): off unless the person turns it on.
 * A device preference only (no personal data); storage can be missing, so every access is guarded.
 */
const KEY = "la_lanh_month_weekly_reminder";

export function monthReminderOn(): boolean {
  try {
    return localStorage.getItem(KEY) === "on";
  } catch {
    return false;
  }
}

export function setMonthReminder(on: boolean): void {
  try {
    if (on) localStorage.setItem(KEY, "on");
    else localStorage.removeItem(KEY);
  } catch {
    // Storage blocked: the reminder simply stays off.
  }
}

/** Monday in Vietnam time, the only day the Home line shows. */
export function isMondayInVietnam(now: Date = new Date()): boolean {
  const weekday = new Intl.DateTimeFormat("en-US", { timeZone: "Asia/Ho_Chi_Minh", weekday: "short" }).format(now);
  return weekday === "Mon";
}
