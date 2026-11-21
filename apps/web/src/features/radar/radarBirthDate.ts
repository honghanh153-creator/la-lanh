/** "YYYY-MM-DD" for a real calendar date of someone aged 18 to 120, else null. */
export function adultBirthDate(day: string, month: string, year: string): string | null {
  if (!/^\d{1,2}$/.test(day) || !/^\d{1,2}$/.test(month) || !/^\d{4}$/.test(year)) return null;
  const dayValue = Number(day);
  const monthValue = Number(month);
  const yearValue = Number(year);
  const value = new Date(Date.UTC(yearValue, monthValue - 1, dayValue));
  if (value.getUTCDate() !== dayValue || value.getUTCMonth() !== monthValue - 1 || value.getUTCFullYear() !== yearValue) return null;
  const today = new Date();
  let age = today.getUTCFullYear() - yearValue;
  if (today.getUTCMonth() < monthValue - 1 || (today.getUTCMonth() === monthValue - 1 && today.getUTCDate() < dayValue)) age -= 1;
  if (age < 18 || age > 120) return null;
  return `${year}-${String(monthValue).padStart(2, "0")}-${String(dayValue).padStart(2, "0")}`;
}
